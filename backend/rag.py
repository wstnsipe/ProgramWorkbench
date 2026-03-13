"""pgvector retrieval for program knowledge.

Provides:
  embed_text(text, db) -> list[float]   # DB-cached via embedding_cache table
  retrieve_chunks(db, program_id, query, k) -> list[dict]
"""
from __future__ import annotations

import hashlib
import os
import time

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

_EMBED_MODEL_DEFAULT = "text-embedding-3-small"


def _embed_model() -> str:
    return os.environ.get("OPENAI_EMBED_MODEL", _EMBED_MODEL_DEFAULT)


def _cache_key(model: str, text: str) -> str:
    """SHA-256 of '<model>:<text>' for the embedding_cache table."""
    return hashlib.sha256(f"{model}:{text}".encode()).hexdigest()


def embed_text(text: str, db: Session | None = None) -> list[float]:
    """Embed a single string, using the DB cache when a session is provided.

    Cache key = sha256(model + ":" + text).
    Raises ValueError on missing API key or API failure.
    """
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    model = _embed_model()

    # --- cache lookup ---
    if db is not None:
        key = _cache_key(model, text)
        row = db.execute(
            sa_text("SELECT embedding FROM embedding_cache WHERE key = :k"),
            {"k": key},
        ).fetchone()
        if row is not None:
            print(f"[rag] embed cache HIT  model={model} key={key[:12]}…")
            # pgvector returns the vector as a Python list via the driver
            return list(row.embedding)

    # --- API call ---
    t0 = time.perf_counter()
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(model=model, input=[text])
        embedding: list[float] = response.data[0].embedding
    except openai.OpenAIError as exc:
        raise ValueError(f"Embedding API error: {exc}") from exc
    elapsed = time.perf_counter() - t0
    print(f"[rag] embed API call  model={model} chars={len(text)} elapsed={elapsed:.2f}s")

    # --- cache store ---
    if db is not None:
        key = _cache_key(model, text)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        try:
            db.execute(
                sa_text(
                    "INSERT INTO embedding_cache (key, embedding) "
                    "VALUES (:k, CAST(:e AS vector)) "
                    "ON CONFLICT (key) DO NOTHING"
                ),
                {"k": key, "e": embedding_str},
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            print(f"[rag] embed cache write failed: {exc}")

    return embedding


def retrieve_chunks(
    db: Session,
    program_id: int,
    query: str,
    k: int = 12,
) -> list[dict]:
    """Vector similarity retrieval over embedded FileChunk rows for a program.

    Embeds `query` (with DB caching), then returns the `k` most similar chunks
    ordered by descending cosine similarity (score = 1 - cosine_distance).

    Returns a list of dicts with keys:
        chunk_text, file_id, filename, chunk_index, source_type, score

    Raises ValueError if no embeddings exist for the program or on API error.
    """
    # Verify at least one embedded chunk exists for this program
    count_sql = sa_text(
        "SELECT COUNT(*) FROM file_chunks "
        "WHERE program_id = :pid AND embedding IS NOT NULL"
    )
    count = db.execute(count_sql, {"pid": program_id}).scalar()
    if not count:
        raise ValueError(
            "No embedded chunks found for this program. "
            "Run POST /programs/{id}/knowledge/index first."
        )

    embedding = embed_text(query, db=db)
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    sql = sa_text("""
        SELECT
            fc.chunk_text,
            fc.file_id,
            pf.filename,
            fc.chunk_index,
            fc.source_type,
            1.0 - (fc.embedding <=> CAST(:qvec AS vector)) AS score
        FROM file_chunks fc
        JOIN program_files pf ON pf.id = fc.file_id
        WHERE fc.program_id = :program_id
          AND fc.embedding IS NOT NULL
        ORDER BY fc.embedding <=> CAST(:qvec AS vector) ASC
        LIMIT :k
    """)

    rows = db.execute(
        sql,
        {"qvec": embedding_str, "program_id": program_id, "k": k},
    ).fetchall()

    results = [
        {
            "chunk_text": row.chunk_text,
            "file_id": row.file_id,
            "filename": row.filename,
            "chunk_index": row.chunk_index,
            "source_type": row.source_type,
            "score": float(row.score),
        }
        for row in rows
    ]
    print(
        f"[rag] retrieve_chunks  program_id={program_id} k_requested={k} "
        f"k_returned={len(results)} model={_embed_model()}"
    )
    return results

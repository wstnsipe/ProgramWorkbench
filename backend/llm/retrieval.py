"""Chunk retrieval for RAG: keyword-based (RagChunk) and vector-based (FileChunk).

Keyword retrieval works over:
  - RagChunk rows for the current program (program_id = program_id)
  - RagChunk rows for global reference docs (program_id IS NULL)

Vector retrieval works over FileChunk rows that have been embedded via
POST /programs/{id}/knowledge/index.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Chunk parameters for the keyword RAG pipeline (RagChunk)
# ---------------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ---------------------------------------------------------------------------
# Chunk parameters for the vector embedding pipeline (FileChunk)
# ---------------------------------------------------------------------------
VECTOR_CHUNK_SIZE = 1000
VECTOR_CHUNK_OVERLAP = 100

# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def index_reference_docs(
    ref_docs_dir: Path,
    db,
    extract_fn: Callable[[Path, str], str],
) -> int:
    """Index files in ref_docs_dir as global RagChunks (program_id=None).

    Skips silently if global chunks already exist.  Returns count of new chunks.
    """
    from models import RagChunk

    existing = db.query(RagChunk).filter(RagChunk.program_id.is_(None)).count()
    if existing > 0:
        return 0

    if not ref_docs_dir.exists():
        return 0

    allowed = {".docx", ".doc", ".pdf", ".txt", ".md"}
    total = 0
    for fpath in sorted(ref_docs_dir.iterdir()):
        if not fpath.is_file():
            continue
        ext = fpath.suffix.lower()
        if ext not in allowed:
            continue
        try:
            text = extract_fn(fpath, ext)
        except Exception:
            continue
        for i, chunk in enumerate(_chunk_text(text)):
            db.add(
                RagChunk(
                    program_id=None,
                    source_filename=fpath.name,
                    chunk_index=i,
                    chunk_text=chunk,
                )
            )
            total += 1

    if total:
        db.commit()
    return total


def index_program_files(program_id: int, files: list, db) -> int:
    """(Re-)index uploaded program files into RagChunk for a given program.

    Deletes existing program RagChunks and rebuilds from current extracted_text.
    Returns count of new chunks.
    """
    from models import RagChunk

    db.query(RagChunk).filter(RagChunk.program_id == program_id).delete()
    total = 0
    for f in files:
        text = f.extracted_text or ""
        for i, chunk in enumerate(_chunk_text(text)):
            db.add(
                RagChunk(
                    program_id=program_id,
                    source_filename=f.filename,
                    chunk_index=i,
                    chunk_text=chunk,
                )
            )
            total += 1
    if total or True:  # always commit to flush deletes
        db.commit()
    return total


def retrieve_chunks(
    queries: list[str],
    db,
    program_id: int,
    top_k: int = 12,
) -> list[dict]:
    """Keyword-based retrieval over program-specific and global RagChunks.

    Scores each chunk by summing term-frequency hits across all queries.
    Returns top_k unique chunks sorted by descending score.
    """
    from models import RagChunk
    from sqlalchemy import or_

    rows = (
        db.query(RagChunk)
        .filter(
            or_(
                RagChunk.program_id == program_id,
                RagChunk.program_id.is_(None),
            )
        )
        .all()
    )

    scored: dict[int, dict] = {}
    for query in queries:
        q_lower = query.lower()
        for row in rows:
            count = row.chunk_text.lower().count(q_lower)
            if count == 0:
                continue
            if row.id not in scored:
                scored[row.id] = {
                    "id": row.id,
                    "source_filename": row.source_filename,
                    "chunk_text": row.chunk_text,
                    "score": 0,
                }
            scored[row.id]["score"] += count

    results = sorted(scored.values(), key=lambda x: -x["score"])
    return results[:top_k]


# ---------------------------------------------------------------------------
# Vector embedding helpers
# ---------------------------------------------------------------------------

def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Compute embeddings for texts using OpenAI text-embedding-3-small.

    Processes in batches of `batch_size` to stay within API limits.
    Returns embeddings in the same order as the input list.
    """
    import openai

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        all_embeddings.extend(item.embedding for item in response.data)
    return all_embeddings


def retrieve_chunks_vector(
    program_id: int,
    query: str,
    db,
    source_type: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    """Vector similarity search over embedded FileChunk rows for a program.

    Embeds `query`, then retrieves the `top_k` most similar chunks ordered by
    cosine distance.  Pass `source_type` to restrict results to
    ``'program_input'`` or ``'exemplar'`` files.

    Returns a list of dicts with keys:
        id, chunk_text, chunk_index, source_type, filename, distance
    """
    from sqlalchemy import text as sa_text

    query_embedding = embed_texts([query])[0]
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    sql = sa_text("""
        SELECT
            fc.id,
            fc.chunk_text,
            fc.chunk_index,
            fc.source_type,
            pf.filename,
            fc.embedding <=> CAST(:embedding AS vector) AS distance
        FROM file_chunks fc
        JOIN program_files pf ON pf.id = fc.file_id
        WHERE fc.program_id = :program_id
          AND fc.embedding IS NOT NULL
          AND (:source_type IS NULL OR fc.source_type = :source_type)
        ORDER BY fc.embedding <=> CAST(:embedding AS vector) ASC
        LIMIT :top_k
    """)

    rows = db.execute(
        sql,
        {
            "embedding": embedding_str,
            "program_id": program_id,
            "source_type": source_type,
            "top_k": top_k,
        },
    ).fetchall()

    return [
        {
            "id": row.id,
            "chunk_text": row.chunk_text,
            "chunk_index": row.chunk_index,
            "source_type": row.source_type,
            "filename": row.filename,
            "distance": float(row.distance),
        }
        for row in rows
    ]

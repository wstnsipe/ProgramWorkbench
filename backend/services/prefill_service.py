"""prefill_service.py — RAG + LLM extraction of suggested field values from uploaded docs."""
from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

# Fields to attempt prefill, in display order
PREFILL_FIELDS: list[dict] = [
    {
        "field": "program_description",
        "label": "Program Description",
        "queries": ["program description", "system description", "purpose", "mission"],
        "instruction": (
            "Extract a 2–4 sentence program description from the excerpts. "
            "Plain prose, no bullets. Government English."
        ),
    },
    {
        "field": "f_tech_challenges_and_risk_areas",
        "label": "Technical Challenges & Risk Areas",
        "queries": ["technical risk", "technology risk", "challenges", "development risk"],
        "instruction": (
            "Summarize technical challenges and risk areas mentioned. "
            "2–4 sentences or a short bulleted list."
        ),
    },
    {
        "field": "e_similar_previous_programs",
        "label": "Similar / Previous Programs",
        "queries": ["similar program", "legacy system", "predecessor", "existing system"],
        "instruction": (
            "List similar or predecessor programs mentioned. "
            "One sentence or a short bulleted list."
        ),
    },
]

SCORE_HIGH_THRESHOLD = 3  # keyword hit count for "high" confidence


@dataclass
class PrefillSuggestion:
    field: str
    label: str
    suggested_value: str
    confidence: str        # "high" | "low"
    source_excerpt: str    # first 200 chars of best-matching chunk


@dataclass
class PrefillResult:
    suggestions: list[PrefillSuggestion]
    has_source_docs: bool
    chunks_used: int


def run_prefill(program_id: int, db: Session) -> PrefillResult:
    """Retrieve chunks and ask LLM to extract field values. No pgvector required."""
    from llm.retrieval import retrieve_chunks  # keyword-based, uses RagChunk table
    from llm.client import get_openai_client
    from models import RagChunk
    from sqlalchemy import or_

    has_docs = (
        db.query(RagChunk)
        .filter(or_(RagChunk.program_id == program_id, RagChunk.program_id.is_(None)))
        .count()
        > 0
    )

    if not has_docs:
        return PrefillResult(suggestions=[], has_source_docs=False, chunks_used=0)

    client = get_openai_client()
    suggestions: list[PrefillSuggestion] = []
    total_chunks = 0

    for fdef in PREFILL_FIELDS:
        chunks = retrieve_chunks(fdef["queries"], db, program_id, top_k=6)
        if not chunks:
            continue

        total_chunks += len(chunks)
        best_score: int = chunks[0]["score"]
        source_excerpt: str = chunks[0]["chunk_text"][:200]
        chunk_block = "\n\n---\n\n".join(c["chunk_text"][:800] for c in chunks[:4])

        prompt = f"""You are extracting program acquisition information from government documents.

TASK: {fdef["instruction"]}

RETRIEVED DOCUMENT EXCERPTS:
{chunk_block}

Respond with a JSON object exactly like:
{{"value": "<extracted text or empty string>", "found": true}}

Rules:
- Only include information clearly present in the excerpts. Do not invent.
- If not found, set found=false and value="".
- Keep extracted text concise (≤150 words).
- Plain government English."""

        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=400,
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            if data.get("found") and data.get("value"):
                suggestions.append(
                    PrefillSuggestion(
                        field=fdef["field"],
                        label=fdef["label"],
                        suggested_value=str(data["value"]).strip(),
                        confidence="high" if best_score >= SCORE_HIGH_THRESHOLD else "low",
                        source_excerpt=source_excerpt,
                    )
                )
        except Exception:
            continue  # silently skip — prefill is advisory only

    return PrefillResult(
        suggestions=suggestions,
        has_source_docs=has_docs,
        chunks_used=total_chunks,
    )

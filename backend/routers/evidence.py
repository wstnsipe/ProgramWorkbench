"""
GET /programs/{id}/evidence?context=brief — Keyword chunk retrieval for the side panel.

Returns top document chunks relevant to the given context (tab name).
No LLM call — pure keyword retrieval over RagChunk rows.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import get_db

router = APIRouter(prefix="/programs/{program_id}/evidence", tags=["evidence"])

# Tab → search terms
_CONTEXT_QUERIES: dict[str, list[str]] = {
    "brief":   ["program description", "mission", "purpose", "objective", "requirements"],
    "modules": ["module", "subsystem", "component", "architecture", "interface"],
    "upload":  ["program", "system", "requirement"],
    "documents": ["acquisition", "strategy", "contract", "schedule"],
    "default": ["program", "system", "requirement", "objective"],
}


class EvidenceChunk(BaseModel):
    source_filename: str
    text: str           # first 300 chars of chunk
    score: int


class EvidenceOut(BaseModel):
    context: str
    chunks: list[EvidenceChunk]
    has_docs: bool


@router.get("", response_model=EvidenceOut)
def get_evidence(
    program_id: int,
    context: str = Query("default"),
    db: Session = Depends(get_db),
):
    prog = db.query(models.Program).filter_by(id=program_id).first()
    if not prog:
        raise HTTPException(404, "Program not found")

    from llm.retrieval import retrieve_chunks
    from sqlalchemy import or_
    from models import RagChunk

    has_docs = (
        db.query(RagChunk)
        .filter(or_(RagChunk.program_id == program_id, RagChunk.program_id.is_(None)))
        .count() > 0
    )

    queries = _CONTEXT_QUERIES.get(context.lower(), _CONTEXT_QUERIES["default"])
    raw = retrieve_chunks(queries, db, program_id, top_k=5)

    chunks = [
        EvidenceChunk(
            source_filename=c["source_filename"],
            text=c["chunk_text"][:300],
            score=c["score"],
        )
        for c in raw
    ]

    return EvidenceOut(context=context, chunks=chunks, has_docs=has_docs)

"""
POST /programs/{id}/prefill — RAG-based field suggestion from uploaded docs.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import get_db
from services.prefill_service import run_prefill

router = APIRouter(prefix="/programs/{program_id}/prefill", tags=["prefill"])


class PrefillSuggestionOut(BaseModel):
    field: str
    label: str
    suggested_value: str
    confidence: str
    source_excerpt: str


class PrefillResultOut(BaseModel):
    suggestions: list[PrefillSuggestionOut]
    has_source_docs: bool
    chunks_used: int


@router.post("", response_model=PrefillResultOut)
def prefill_fields(program_id: int, db: Session = Depends(get_db)):
    """
    POST /programs/{program_id}/prefill

    Searches uploaded docs for content matching key wizard fields and uses
    an LLM to extract suggested values. Returns structured suggestions.
    Requires at least one uploaded + extracted file for the program.
    """
    prog = db.query(models.Program).filter_by(id=program_id).first()
    if not prog:
        raise HTTPException(404, "Program not found")

    result = run_prefill(program_id, db)
    return PrefillResultOut(
        suggestions=[PrefillSuggestionOut(**vars(s)) for s in result.suggestions],
        has_source_docs=result.has_source_docs,
        chunks_used=result.chunks_used,
    )

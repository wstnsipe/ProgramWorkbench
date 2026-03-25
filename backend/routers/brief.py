"""
/programs/{id}/brief — Program brief (structured fields).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from contracts import BriefIn, BriefOut

router = APIRouter(prefix="/programs/{program_id}/brief", tags=["brief"])


def _require_program(program_id: int, db: Session):
    if not db.query(models.Program).filter_by(id=program_id).first():
        raise HTTPException(404, "Program not found")


@router.get("", response_model=BriefOut)
def get_brief(program_id: int, db: Session = Depends(get_db)):
    """GET /programs/{program_id}/brief"""
    _require_program(program_id, db)
    brief = db.query(models.ProgramBrief).filter_by(program_id=program_id).first()
    if not brief:
        raise HTTPException(404, "Brief not found")
    return brief


@router.put("", response_model=BriefOut)
def upsert_brief(program_id: int, payload: BriefIn, db: Session = Depends(get_db)):
    """PUT /programs/{program_id}/brief — create or replace"""
    _require_program(program_id, db)
    brief = db.query(models.ProgramBrief).filter_by(program_id=program_id).first()
    if brief is None:
        brief = models.ProgramBrief(program_id=program_id, **payload.model_dump())
        db.add(brief)
    else:
        for field, value in payload.model_dump().items():
            setattr(brief, field, value)
    db.commit()
    db.refresh(brief)
    return brief

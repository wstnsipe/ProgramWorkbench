"""
/programs/{id}/standards — Standards and architectures.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from contracts import StandardIn as ProgramStandardIn, StandardOut as ProgramStandardOut, StandardsBulkIn

router = APIRouter(prefix="/programs/{program_id}/standards", tags=["standards"])


def _get_model():
    from models_v2 import ProgramStandard
    return ProgramStandard


def _require_program(program_id: int, db: Session):
    import models
    if not db.query(models.Program).filter_by(id=program_id).first():
        raise HTTPException(404, "Program not found")


@router.get("", response_model=List[ProgramStandardOut])
def list_standards(program_id: int, db: Session = Depends(get_db)):
    """GET /programs/{program_id}/standards"""
    _require_program(program_id, db)
    M = _get_model()
    return db.query(M).filter_by(program_id=program_id).all()


@router.put("", response_model=List[ProgramStandardOut], status_code=200)
def replace_standards(
    program_id: int,
    body: StandardsBulkIn,
    db: Session = Depends(get_db),
):
    """
    PUT /programs/{program_id}/standards
    Replace all standards for the program.
    """
    _require_program(program_id, db)
    M = _get_model()

    db.query(M).filter_by(program_id=program_id).delete()

    created = []
    for s in body.standards:
        row = M(
            program_id=program_id,
            standard_name=s.standard_name,
            applies_to_modules=s.applies_to_modules,
            applies_to_interfaces=s.applies_to_interfaces,
            applies=s.applies_to_modules or s.applies_to_interfaces,
            catalog_id=s.catalog_id,
            notes=s.notes,
        )
        db.add(row)
        created.append(row)

    db.commit()
    for row in created:
        db.refresh(row)
    return created

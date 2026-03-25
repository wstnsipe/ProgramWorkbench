"""
/programs/{id}/modules — Module CRUD (bulk replace pattern).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from contracts import ModuleIn as ModuleInV2, ModuleOut as ModuleOutV2, ModulesBulkIn

router = APIRouter(prefix="/programs/{program_id}/modules", tags=["modules"])


@router.get("", response_model=List[ModuleOutV2])
def list_modules(program_id: int, db: Session = Depends(get_db)):
    """GET /programs/{program_id}/modules"""
    _require_program(program_id, db)
    return db.query(models.Module).filter_by(program_id=program_id).all()


@router.put("", response_model=List[ModuleOutV2], status_code=200)
def replace_modules(
    program_id: int,
    body: ModulesBulkIn,
    db: Session = Depends(get_db),
):
    """
    PUT /programs/{program_id}/modules
    Replace ALL modules for the program with the provided list.
    Omit empty rows (name is blank) before persisting.
    """
    _require_program(program_id, db)

    # Delete existing
    db.query(models.Module).filter_by(program_id=program_id).delete()

    # Insert new (skip rows with no name)
    created = []
    for m in body.modules:
        if not m.name or not m.name.strip():
            continue
        row = models.Module(
            program_id=program_id,
            name=m.name.strip(),
            description=m.description,
            rationale=m.rationale,
            key_interfaces=m.key_interfaces,
            standards=m.standards,
            tech_risk=m.tech_risk,
            obsolescence_risk=m.obsolescence_risk,
            cots_candidate=m.cots_candidate,
        )
        # future_recompete only if column exists (post-migration)
        if hasattr(models.Module, "future_recompete"):
            row.future_recompete = m.future_recompete
        db.add(row)
        created.append(row)

    db.commit()
    for row in created:
        db.refresh(row)
    return created


@router.delete("/{module_id}", status_code=204)
def delete_module(program_id: int, module_id: int, db: Session = Depends(get_db)):
    """DELETE /programs/{program_id}/modules/{module_id}"""
    _require_program(program_id, db)
    row = db.query(models.Module).filter_by(id=module_id, program_id=program_id).first()
    if not row:
        raise HTTPException(404, "Module not found")
    db.delete(row)
    db.commit()


def _require_program(program_id: int, db: Session):
    if not db.query(models.Program).filter_by(id=program_id).first():
        raise HTTPException(404, "Program not found")

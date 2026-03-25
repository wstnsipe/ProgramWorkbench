"""
/programs/{id}/scenarios — MOSA scenario management.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from contracts import ScenarioIn as MosaScenarioIn, ScenarioOut as MosaScenarioOut, ScenariosBulkIn

router = APIRouter(prefix="/programs/{program_id}/scenarios", tags=["scenarios"])


def _get_model():
    from models_v2 import MosaScenario
    return MosaScenario


def _require_program(program_id: int, db: Session):
    import models
    if not db.query(models.Program).filter_by(id=program_id).first():
        raise HTTPException(404, "Program not found")


@router.get("", response_model=List[MosaScenarioOut])
def list_scenarios(program_id: int, db: Session = Depends(get_db)):
    """GET /programs/{program_id}/scenarios"""
    _require_program(program_id, db)
    M = _get_model()
    return db.query(M).filter_by(program_id=program_id).all()


@router.put("", response_model=List[MosaScenarioOut], status_code=200)
def replace_scenarios(
    program_id: int,
    body: ScenariosBulkIn,
    db: Session = Depends(get_db),
):
    """
    PUT /programs/{program_id}/scenarios
    Replace all MOSA scenarios for the program.
    """
    _require_program(program_id, db)
    M = _get_model()

    db.query(M).filter_by(program_id=program_id).delete()

    created = []
    for s in body.scenarios:
        description = s.description or ""
        word_count = len(description.split()) if description else 0
        row = M(
            program_id=program_id,
            scenario_type=s.scenario_type,
            module_name=s.module_name,
            description=description,
            word_count=word_count,
        )
        db.add(row)
        created.append(row)

    db.commit()
    for row in created:
        db.refresh(row)
    return created

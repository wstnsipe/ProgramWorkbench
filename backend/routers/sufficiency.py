"""
/programs/{id}/sufficiency — Sufficiency check (no LLM).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from contracts import SufficiencyOut
from services.sufficiency_service import compute_sufficiency

router = APIRouter(prefix="/programs/{program_id}/sufficiency", tags=["sufficiency"])


@router.get("", response_model=SufficiencyOut)
def get_sufficiency(program_id: int, db: Session = Depends(get_db)):
    """
    GET /programs/{program_id}/sufficiency

    Runs sufficiency check + rules engine.
    No LLM calls — pure deterministic scoring.
    Returns level (GREEN/YELLOW_HIGH/YELLOW_LOW/RED), score, gate results,
    field coverage, and rules engine modifiers.
    """
    program = db.query(models.Program).filter_by(id=program_id).first()
    if not program:
        raise HTTPException(404, "Program not found")

    brief = db.query(models.ProgramBrief).filter_by(program_id=program_id).first()
    modules = db.query(models.Module).filter_by(program_id=program_id).all()

    try:
        from models_v2 import MosaScenario, ProgramStandard
        scenarios = db.query(MosaScenario).filter_by(program_id=program_id).all()
        standards = db.query(ProgramStandard).filter_by(program_id=program_id).all()
    except Exception:
        scenarios = []
        standards = []

    file_count = db.query(models.ProgramFile).filter_by(
        program_id=program_id, source_type="program_input"
    ).count()

    result = compute_sufficiency(
        program=program.__dict__,
        brief=brief.__dict__ if brief else None,
        modules=modules,
        scenarios=scenarios,
        standards=standards,
        file_count=file_count,
    )

    # Optionally log to sufficiency_logs table
    _log_result(program_id, result, db)

    return SufficiencyOut(
        level=result.level.value,
        score=result.score,
        gates=[{"gate_id": g.gate_id, "passed": g.passed, "message": g.message} for g in result.gates],
        coverage=[
            {
                "field_id": c.field_id,
                "label": c.label,
                "weight": c.weight,
                "present": c.present,
                "source": c.source,
            }
            for c in result.coverage
        ],
        missing_critical=result.missing_critical,
        warnings=result.warnings,
        mig_id=result.mig_id,
        modifiers=result.modifiers,
        rule_violations=result.rule_violations,
    )


def _log_result(program_id: int, result, db: Session):
    try:
        import json
        from models_v2 import SufficiencyLog
        gates_failed = [g.gate_id for g in result.gates if not g.passed]
        row = SufficiencyLog(
            program_id=program_id,
            level=result.level.value,
            score=result.score,
            gates_failed_json=json.dumps(gates_failed),
        )
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()

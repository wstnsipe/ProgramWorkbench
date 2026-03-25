"""
/programs/{id}/wizard — Wizard Q&A answers (key-value store).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from contracts import WizardOut, WizardQuestionOut as QuestionOut, WizardAnswersIn as WizardAnswersSaveIn

router = APIRouter(prefix="/programs/{program_id}/wizard", tags=["wizard"])


@router.get("", response_model=WizardOut)
def get_wizard(program_id: int, db: Session = Depends(get_db)):
    """
    GET /programs/{program_id}/wizard
    Returns current wizard answers + question list with missing flags.
    Delegates to existing wizard logic in main.py (or extracted service).
    """
    _require_program(program_id, db)
    # Import existing wizard builder to avoid duplication
    from main import _build_wizard_out  # type: ignore
    return _build_wizard_out(program_id, db)


@router.put("", status_code=204)
def save_wizard_answers(
    program_id: int,
    body: WizardAnswersSaveIn,
    db: Session = Depends(get_db),
):
    """
    PUT /programs/{program_id}/wizard
    Upsert wizard answer key-value pairs.
    Partial update: only keys present in body.answers are written.
    Special handling for g_mosa_scenarios (JSON list).
    """
    _require_program(program_id, db)
    for question_id, answer_val in body.answers.items():
        import json as _json
        answer_text = (
            _json.dumps(answer_val)
            if isinstance(answer_val, (list, dict))
            else (str(answer_val) if answer_val is not None else None)
        )
        existing = (
            db.query(models.ProgramAnswer)
            .filter_by(program_id=program_id, question_id=question_id)
            .first()
        )
        if existing:
            existing.answer_text = answer_text
        else:
            db.add(models.ProgramAnswer(
                program_id=program_id,
                question_id=question_id,
                answer_text=answer_text,
            ))
    db.commit()


def _require_program(program_id: int, db: Session) -> models.Program:
    prog = db.query(models.Program).filter_by(id=program_id).first()
    if not prog:
        raise HTTPException(404, "Program not found")
    return prog

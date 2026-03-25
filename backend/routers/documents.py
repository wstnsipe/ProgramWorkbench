"""
/programs/{id}/documents — Document generation and download.
"""
import os
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
from database import get_db
from contracts import DocumentOut, GenerateDocIn as GenerateDocRequestV2, GenerateDocOut

router = APIRouter(prefix="/programs/{program_id}/documents", tags=["documents"])

OUTPUT_ROOT = os.getenv("OUTPUT_DIR", "data/documents")


def _require_program(program_id: int, db: Session) -> models.Program:
    prog = db.query(models.Program).filter_by(id=program_id).first()
    if not prog:
        raise HTTPException(404, "Program not found")
    return prog


@router.get("", response_model=List[DocumentOut])
def list_documents(program_id: int, db: Session = Depends(get_db)):
    """GET /programs/{program_id}/documents"""
    _require_program(program_id, db)
    return db.query(models.ProgramDocument).filter_by(program_id=program_id).all()


@router.post("/generate", response_model=GenerateDocOut, status_code=202)
def generate_document(
    program_id: int,
    body: GenerateDocRequestV2,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    POST /programs/{program_id}/documents/generate
    Queue section-by-section document generation.
    Returns immediately with job_id; poll /documents/jobs/{job_id} for status.

    doc_type: rfi | acq_strategy | sep | mcp
    """
    prog = _require_program(program_id, db)
    doc_type = body.doc_type.value

    # Quick sufficiency gate check — RED blocks generation
    from services.sufficiency_service import compute_sufficiency
    brief = db.query(models.ProgramBrief).filter_by(program_id=program_id).first()
    modules = db.query(models.Module).filter_by(program_id=program_id).all()
    answers_rows = db.query(models.ProgramAnswer).filter_by(program_id=program_id).all()
    wizard_answers = {r.question_id: r.answer_text for r in answers_rows}
    try:
        from models_v2 import ProgramStandard
        standards = db.query(ProgramStandard).filter_by(program_id=program_id).all()
    except Exception:
        standards = []
    file_count = db.query(models.ProgramFile).filter_by(
        program_id=program_id, source_type="program_input"
    ).count()

    suf = compute_sufficiency(
        program=prog.__dict__,
        brief=brief.__dict__ if brief else None,
        modules=modules,
        wizard_answers=wizard_answers,
        standards=standards,
        file_count=file_count,
    )
    if suf.level.value == "RED":
        gates_failed = [g.message for g in suf.gates if not g.passed]
        raise HTTPException(
            422,
            {
                "detail": "Sufficiency check failed — resolve RED issues before generating.",
                "gates_failed": gates_failed,
            },
        )

    job_id = str(uuid.uuid4())
    output_path = os.path.join(OUTPUT_ROOT, str(program_id), f"{doc_type}_{job_id}.docx")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    background_tasks.add_task(
        _run_generation,
        program_id=program_id,
        doc_type=doc_type,
        output_path=output_path,
        job_id=job_id,
    )

    return GenerateDocOut(
        job_id=job_id,
        status="queued",
        doc_type=doc_type,
        program_id=program_id,
    )


@router.get("/{document_id}/download")
def download_document(
    program_id: int,
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    GET /programs/{program_id}/documents/{document_id}/download
    Stream the .docx file.
    """
    _require_program(program_id, db)
    doc = db.query(models.ProgramDocument).filter_by(
        id=document_id, program_id=program_id
    ).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if not os.path.exists(doc.file_path):
        raise HTTPException(410, "Document file no longer available")
    filename = os.path.basename(doc.file_path)
    return FileResponse(
        doc.file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


# ---------------------------------------------------------------------------
# Background task — runs generation in the background
# ---------------------------------------------------------------------------

def _run_generation(program_id: int, doc_type: str, output_path: str, job_id: str):
    """
    Runs in BackgroundTasks. Imports its own DB session.
    On completion, persists a ProgramDocument record.
    """
    from database import SessionLocal
    db = SessionLocal()
    try:
        import asyncio
        from generation.orchestrator import generate_document as _gen
        # asyncio.run needed because orchestrator is async
        assembled = asyncio.run(_gen(db=db, program_id=program_id, doc_type=doc_type, output_path=output_path))

        # Render to DOCX using existing docx_builder
        _render_to_docx(assembled, doc_type, output_path, program_id, db)

        # Persist record
        doc_row = models.ProgramDocument(
            program_id=program_id,
            doc_type=doc_type,
            file_path=output_path,
        )
        db.add(doc_row)
        db.commit()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(
            "Generation job %s failed: %s", job_id, exc, exc_info=True
        )
        db.rollback()
    finally:
        db.close()


def _render_to_docx(assembled: dict, doc_type: str, output_path: str, program_id: int, db):
    """
    Bridge to existing docx_builder until generation/renderer.py is complete.
    Falls back to calling the existing main.py generation function.
    """
    try:
        from generation.renderer import render_document
        render_document(assembled=assembled, doc_type=doc_type, output_path=output_path)
    except ImportError:
        # Fallback: call existing docx_builder directly
        import docx_builder
        build_fn = getattr(docx_builder, f"build_{doc_type}_docx", None)
        if build_fn:
            build_fn(assembled, output_path)

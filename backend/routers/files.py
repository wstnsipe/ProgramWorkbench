"""
/programs/{id}/files — File upload, extraction, and management.
"""
import os
import shutil
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

import models
from database import get_db
from contracts import FileOut as ProgramFileOut, ExtractionOut as ExtractionResultOut

router = APIRouter(prefix="/programs/{program_id}/files", tags=["files"])

UPLOAD_ROOT = os.getenv("UPLOAD_DIR", "data/uploads")


def _require_program(program_id: int, db: Session) -> models.Program:
    prog = db.query(models.Program).filter_by(id=program_id).first()
    if not prog:
        raise HTTPException(404, "Program not found")
    return prog


@router.post("", response_model=List[ProgramFileOut], status_code=201)
async def upload_files(
    program_id: int,
    files: List[UploadFile] = File(...),
    source_type: str = "program_input",
    db: Session = Depends(get_db),
):
    """
    POST /programs/{program_id}/files
    Upload one or more files (multipart/form-data).
    source_type: "program_input" (default) | "exemplar"
    """
    _require_program(program_id, db)

    program_dir = os.path.join(UPLOAD_ROOT, str(program_id))
    os.makedirs(program_dir, exist_ok=True)

    created = []
    for upload in files:
        dest = os.path.join(program_dir, upload.filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        size = os.path.getsize(dest)
        relative_path = os.path.join(str(program_id), upload.filename)

        row = models.ProgramFile(
            program_id=program_id,
            filename=upload.filename,
            relative_path=relative_path,
            size_bytes=size,
            source_type=source_type,
        )
        db.add(row)
        created.append(row)

    db.commit()
    for row in created:
        db.refresh(row)
    return created


@router.post("/{file_id}/extract", response_model=ExtractionResultOut)
def extract_file(
    program_id: int,
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    POST /programs/{program_id}/files/{file_id}/extract
    Run text extraction and chunking for a single file.
    Idempotent — re-extracts if called again.
    """
    _require_program(program_id, db)
    file_row = db.query(models.ProgramFile).filter_by(id=file_id, program_id=program_id).first()
    if not file_row:
        raise HTTPException(404, "File not found")

    # Delegate to existing extraction logic
    try:
        from llm.retrieval import extract_and_chunk_file
        result = extract_and_chunk_file(db=db, file_row=file_row)
        return ExtractionResultOut(
            file_id=file_id,
            filename=file_row.filename,
            chars_extracted=result.get("chars", 0),
            chunks_created=result.get("chunks", 0),
        )
    except Exception as exc:
        return ExtractionResultOut(
            file_id=file_id,
            filename=file_row.filename,
            chars_extracted=0,
            chunks_created=0,
            error=str(exc),
        )


@router.delete("/{file_id}", status_code=204)
def delete_file(program_id: int, file_id: int, db: Session = Depends(get_db)):
    """DELETE /programs/{program_id}/files/{file_id}"""
    _require_program(program_id, db)
    row = db.query(models.ProgramFile).filter_by(id=file_id, program_id=program_id).first()
    if not row:
        raise HTTPException(404, "File not found")
    # Remove physical file
    full_path = os.path.join(UPLOAD_ROOT, row.relative_path)
    if os.path.exists(full_path):
        os.remove(full_path)
    db.delete(row)
    db.commit()

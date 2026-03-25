"""
/programs — Program CRUD + service branch / MIG management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from contracts import ProgramIn, ProgramPatch, ProgramOut

# Aliases used in route signatures
ProgramCreateV2 = ProgramIn
ProgramUpdateV2 = ProgramPatch
ProgramOutV2    = ProgramOut

router = APIRouter(prefix="/programs", tags=["programs"])


@router.post("", response_model=ProgramOutV2, status_code=201)
def create_program(body: ProgramCreateV2, db: Session = Depends(get_db)):
    """
    POST /programs
    Create a new program. Optionally set service_branch and army_pae at creation time.
    """
    program = models.Program(name=body.name)
    # Assign new columns if they exist on the model (post-migration)
    if hasattr(models.Program, "service_branch"):
        program.service_branch = body.service_branch
        program.army_pae = body.army_pae
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


@router.get("/{program_id}", response_model=ProgramOutV2)
def get_program(program_id: int, db: Session = Depends(get_db)):
    """GET /programs/{program_id}"""
    prog = db.query(models.Program).filter_by(id=program_id).first()
    if not prog:
        raise HTTPException(404, "Program not found")
    return prog


@router.patch("/{program_id}", response_model=ProgramOutV2)
def update_program(program_id: int, body: ProgramUpdateV2, db: Session = Depends(get_db)):
    """
    PATCH /programs/{program_id}
    Update name, service_branch, or army_pae.
    After updating service_branch, client should re-fetch /sufficiency to get updated mig_id.
    """
    prog = db.query(models.Program).filter_by(id=program_id).first()
    if not prog:
        raise HTTPException(404, "Program not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        if hasattr(prog, field):
            setattr(prog, field, val)
    db.commit()
    db.refresh(prog)
    return prog

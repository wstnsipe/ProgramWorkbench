from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class ProgramBrief(Base):
    __tablename__ = "program_briefs"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, unique=True, index=True)
    program_description = Column(Text, nullable=True)
    dev_cost_estimate = Column(Float, nullable=True)
    production_unit_cost = Column(Float, nullable=True)
    attritable = Column(Boolean, nullable=True)
    sustainment_tail = Column(Boolean, nullable=True)
    software_large_part = Column(Boolean, nullable=True)
    mission_critical = Column(Boolean, nullable=True)
    safety_critical = Column(Boolean, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)


class ProgramFile(Base):
    __tablename__ = "program_files"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    relative_path = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    extracted_text = Column(Text, nullable=True)
    source_type = Column(String, nullable=False, server_default="program_input", default="program_input")


class ProgramAnswer(Base):
    __tablename__ = "program_answers"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    question_id = Column(String, nullable=False, index=True)
    answer_text = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("program_id", "question_id", name="uq_program_question"),)


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    key_interfaces = Column(Text, nullable=True)
    standards = Column(Text, nullable=True)
    tech_risk = Column(Boolean, nullable=False, default=False)
    obsolescence_risk = Column(Boolean, nullable=False, default=False)
    cots_candidate = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProgramDocument(Base):
    __tablename__ = "program_documents"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    doc_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FileText(Base):
    __tablename__ = "file_text"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("program_files.id"), nullable=False, unique=True, index=True)
    extracted_text = Column(Text, nullable=False, default="")
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FileChunk(Base):
    __tablename__ = "file_chunks"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("program_files.id"), nullable=False, index=True)
    source_type = Column(String, nullable=False, server_default="program_input", default="program_input")
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RagChunk(Base):
    """Chunks used by the RAG pipeline.

    program_id is NULL for global reference documents (backend/reference_docs/).
    program_id is set for chunks derived from program-specific uploaded files.
    """
    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)
    source_filename = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

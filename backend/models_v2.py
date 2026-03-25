"""
models_v2.py — Additive schema extensions.

These models extend the existing models.py without breaking it.
Migration path: add Alembic migration to ALTER existing tables and CREATE new ones.

New tables:
  - mosa_scenarios
  - program_standards
  - exemplar_styles
  - sufficiency_logs

New columns on existing tables (via Alembic migration):
  - programs: service_branch, army_pae, army_branch, mig_id
  - program_briefs: timeline_months, similar_programs_exist, software_involved
  - modules: future_recompete
  - file_chunks: is_heading, is_table, is_list, section_heading, doc_section, fact_score
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey,
    DateTime, Text, UniqueConstraint,
)
from sqlalchemy.sql import func
from database import Base


# ---------------------------------------------------------------------------
# New standalone tables
# ---------------------------------------------------------------------------

class MosaScenario(Base):
    """Structured MOSA scenario: reprocure / reuse / recompete."""
    __tablename__ = "mosa_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    # One of: reprocure, reuse, recompete
    scenario_type = Column(String, nullable=False)
    module_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)


class ProgramStandard(Base):
    """Standards and architectures applicable to the program."""
    __tablename__ = "program_standards"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    standard_name = Column(String, nullable=False)
    applies = Column(Boolean, nullable=False, default=True)
    applies_to_modules = Column(Boolean, nullable=False, default=False, server_default='false')
    applies_to_interfaces = Column(Boolean, nullable=False, default=False, server_default='false')
    # catalog_id for future recommendation-hook integration
    catalog_id = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExemplarStyle(Base):
    """
    Cached per-section style excerpts extracted from exemplar files at upload time.
    Avoids re-extracting on every generation call.
    """
    __tablename__ = "exemplar_styles"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("program_files.id"), nullable=False, index=True)
    # doc_type: rfi | sep | acq_strategy | mcp
    doc_type = Column(String, nullable=False)
    section_name = Column(String, nullable=False)
    style_excerpt = Column(Text, nullable=False)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("file_id", "doc_type", "section_name", name="uq_exemplar_style"),
    )


class SufficiencyLog(Base):
    """Audit log of sufficiency check results."""
    __tablename__ = "sufficiency_logs"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    level = Column(String, nullable=False)   # GREEN | YELLOW_HIGH | YELLOW_LOW | RED
    score = Column(Float, nullable=False)
    gates_failed_json = Column(Text, nullable=True)   # JSON list of gate_id strings
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ---------------------------------------------------------------------------
# Alembic migration stub
# (Run these as raw SQL or generate with `alembic revision --autogenerate`)
# ---------------------------------------------------------------------------

MIGRATION_SQL = """
-- programs
ALTER TABLE programs ADD COLUMN IF NOT EXISTS service_branch VARCHAR;
ALTER TABLE programs ADD COLUMN IF NOT EXISTS army_pae VARCHAR;
ALTER TABLE programs ADD COLUMN IF NOT EXISTS army_branch VARCHAR;
ALTER TABLE programs ADD COLUMN IF NOT EXISTS mig_id VARCHAR;

-- program_briefs
ALTER TABLE program_briefs ADD COLUMN IF NOT EXISTS timeline_months INTEGER;
ALTER TABLE program_briefs ADD COLUMN IF NOT EXISTS similar_programs_exist BOOLEAN;
ALTER TABLE program_briefs ADD COLUMN IF NOT EXISTS software_involved BOOLEAN;

-- modules
ALTER TABLE modules ADD COLUMN IF NOT EXISTS future_recompete BOOLEAN NOT NULL DEFAULT FALSE;

-- file_chunks (structure-aware chunking metadata)
ALTER TABLE file_chunks ADD COLUMN IF NOT EXISTS is_heading BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE file_chunks ADD COLUMN IF NOT EXISTS is_table BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE file_chunks ADD COLUMN IF NOT EXISTS is_list BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE file_chunks ADD COLUMN IF NOT EXISTS section_heading VARCHAR;
ALTER TABLE file_chunks ADD COLUMN IF NOT EXISTS doc_section VARCHAR;
ALTER TABLE file_chunks ADD COLUMN IF NOT EXISTS fact_score FLOAT;
"""

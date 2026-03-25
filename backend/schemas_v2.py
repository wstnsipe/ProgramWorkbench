"""
schemas_v2.py — Additive Pydantic schemas for new endpoints.

Import from here alongside existing schemas.py.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ---------------------------------------------------------------------------
# Program (extended)
# ---------------------------------------------------------------------------

class ServiceBranch(str, Enum):
    USN = "USN"
    USAF = "USAF"
    USSF = "USSF"
    ARMY = "ARMY"


class ProgramCreateV2(BaseModel):
    name: str
    service_branch: Optional[ServiceBranch] = None
    army_pae: Optional[str] = None


class ProgramUpdateV2(BaseModel):
    name: Optional[str] = None
    service_branch: Optional[ServiceBranch] = None
    army_pae: Optional[str] = None


class ProgramOutV2(BaseModel):
    id: int
    name: str
    service_branch: Optional[str] = None
    army_pae: Optional[str] = None
    mig_id: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# ProgramBrief (extended)
# ---------------------------------------------------------------------------

class ProgramBriefInV2(BaseModel):
    program_description: Optional[str] = None
    dev_cost_estimate: Optional[float] = None
    production_unit_cost: Optional[float] = None
    timeline_months: Optional[int] = None
    attritable: Optional[bool] = None
    sustainment_tail: Optional[bool] = None
    software_large_part: Optional[bool] = None
    software_involved: Optional[bool] = None
    mission_critical: Optional[bool] = None
    safety_critical: Optional[bool] = None
    similar_programs_exist: Optional[bool] = None


class ProgramBriefOutV2(ProgramBriefInV2):
    program_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Module (extended)
# ---------------------------------------------------------------------------

class ModuleInV2(BaseModel):
    name: str
    description: Optional[str] = None
    rationale: Optional[str] = None
    key_interfaces: Optional[str] = None
    standards: Optional[str] = None
    tech_risk: bool = False
    obsolescence_risk: bool = False
    cots_candidate: bool = False
    future_recompete: bool = False


class ModuleOutV2(ModuleInV2):
    id: int
    program_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ModulesBulkIn(BaseModel):
    """Replace all modules for a program in one call."""
    modules: List[ModuleInV2]


# ---------------------------------------------------------------------------
# MOSA Scenarios
# ---------------------------------------------------------------------------

class ScenarioType(str, Enum):
    REPROCURE = "reprocure"
    REUSE = "reuse"
    RECOMPETE = "recompete"


class MosaScenarioIn(BaseModel):
    scenario_type: ScenarioType
    module_name: Optional[str] = None
    description: Optional[str] = None


class MosaScenarioOut(MosaScenarioIn):
    id: int
    program_id: int
    word_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScenariosBulkIn(BaseModel):
    """Replace all scenarios for a program in one call."""
    scenarios: List[MosaScenarioIn]


# ---------------------------------------------------------------------------
# Standards
# ---------------------------------------------------------------------------

class ProgramStandardIn(BaseModel):
    standard_name: str
    applies: bool = True
    catalog_id: Optional[str] = None
    notes: Optional[str] = None


class ProgramStandardOut(ProgramStandardIn):
    id: int
    program_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StandardsBulkIn(BaseModel):
    """Replace all standards for a program in one call."""
    standards: List[ProgramStandardIn]


# ---------------------------------------------------------------------------
# Sufficiency
# ---------------------------------------------------------------------------

class GateResultOut(BaseModel):
    gate_id: str
    passed: bool
    message: str


class FieldCoverageOut(BaseModel):
    field_id: str
    label: str
    weight: float
    present: bool
    source: str


class SufficiencyOut(BaseModel):
    level: str   # GREEN | YELLOW_HIGH | YELLOW_LOW | RED
    score: float
    gates: List[GateResultOut]
    coverage: List[FieldCoverageOut]
    missing_critical: List[str]
    warnings: List[str]
    # Rules engine output embedded
    mig_id: Optional[str] = None
    modifiers: List[str] = Field(default_factory=list)
    rule_violations: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Document generation
# ---------------------------------------------------------------------------

class DocType(str, Enum):
    RFI = "rfi"
    ACQ_STRATEGY = "acq_strategy"
    SEP = "sep"
    MCP = "mcp"


class GenerateDocRequestV2(BaseModel):
    doc_type: DocType
    # Optional: force regeneration even if doc exists
    force: bool = False


class GenerateDocOut(BaseModel):
    job_id: str
    status: str   # queued | generating | done | error
    doc_type: str
    program_id: int
    document_id: Optional[int] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# File extraction
# ---------------------------------------------------------------------------

class ExtractionResultOut(BaseModel):
    file_id: int
    filename: str
    chars_extracted: int
    chunks_created: int
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Wizard answers (unchanged shape, typed for clarity)
# ---------------------------------------------------------------------------

class WizardAnswersSaveIn(BaseModel):
    """
    Key-value dict of wizard answers.
    Special keys:
      - g_mosa_scenarios: JSON string of list[{type, module_name, description}]
      - g_modules: JSON string of list[ModuleInV2] (legacy path; prefer /modules endpoint)
    """
    answers: Dict[str, Any]

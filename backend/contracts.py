"""
contracts.py — Canonical Pydantic schemas for the APW API.

Single source of truth. All routers import from here.
Replaces schemas.py + schemas_v2.py going forward.

Naming rules
------------
- Input schemas  (POST/PUT body)  → <Resource>In
- Output schemas (GET/POST response) → <Resource>Out
- Bulk replace payloads           → <Resource>sBulkIn
- snake_case everywhere
- No "V2" suffixes — this IS the current version
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import re
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class ServiceBranch(str, Enum):
    USN  = "USN"
    USAF = "USAF"
    USSF = "USSF"
    ARMY = "ARMY"


class DocType(str, Enum):
    RFI          = "rfi"
    ACQ_STRATEGY = "acq_strategy"
    SEP          = "sep"
    MCP          = "mcp"


class ScenarioType(str, Enum):
    REPROCURE = "reprocure"
    REUSE     = "reuse"
    RECOMPETE = "recompete"


class SufficiencyLevel(str, Enum):
    GREEN       = "GREEN"
    YELLOW_HIGH = "YELLOW_HIGH"
    YELLOW_LOW  = "YELLOW_LOW"
    RED         = "RED"


class GenerationStatus(str, Enum):
    QUEUED     = "queued"
    GENERATING = "generating"
    DONE       = "done"
    ERROR      = "error"


class FileSourceType(str, Enum):
    PROGRAM_INPUT = "program_input"
    EXEMPLAR      = "exemplar"


# ─────────────────────────────────────────────────────────────────────────────
# Program
# ─────────────────────────────────────────────────────────────────────────────

class ProgramIn(BaseModel):
    """POST /programs"""
    name: str
    service_branch: Optional[ServiceBranch] = None
    army_pae: Optional[str] = None


class ProgramPatch(BaseModel):
    """PATCH /programs/{id}"""
    name: Optional[str] = None
    service_branch: Optional[ServiceBranch] = None
    army_pae: Optional[str] = None


class ProgramOut(BaseModel):
    """GET /programs / POST /programs response"""
    id: int
    name: str
    service_branch: Optional[str] = None
    army_pae: Optional[str] = None
    mig_id: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Program Brief
# ─────────────────────────────────────────────────────────────────────────────

class BriefIn(BaseModel):
    """PUT /programs/{id}/brief"""
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


class BriefOut(BriefIn):
    """GET /programs/{id}/brief response"""
    program_id: int
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Module
# ─────────────────────────────────────────────────────────────────────────────

class ModuleIn(BaseModel):
    """Single module entry (used inside ModulesBulkIn)"""
    name: str
    description: Optional[str] = None
    rationale: Optional[str] = None
    key_interfaces: Optional[str] = None
    standards: Optional[str] = None          # per-module free text (≠ program_standards table)
    tech_risk: bool = False
    obsolescence_risk: bool = False
    cots_candidate: bool = False
    future_recompete: bool = False


class ModuleOut(ModuleIn):
    """GET /programs/{id}/modules list item"""
    id: int
    program_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ModulesBulkIn(BaseModel):
    """PUT /programs/{id}/modules — replaces all modules atomically"""
    modules: List[ModuleIn]


# ─────────────────────────────────────────────────────────────────────────────
# MOSA Scenarios
# ─────────────────────────────────────────────────────────────────────────────

_MOSA_FORMAT_RE = re.compile(
    r'^For the .+ module, the USG desires the ability to ', re.IGNORECASE
)


class ScenarioIn(BaseModel):
    """Single scenario (used inside ScenariosBulkIn)"""
    scenario_type: ScenarioType
    module_name: Optional[str] = None
    description: Optional[str] = None

    @field_validator('description')
    @classmethod
    def description_format(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip() and not _MOSA_FORMAT_RE.match(v.strip()):
            raise ValueError(
                'Scenario description must start with: '
                '"For the [module name] module, the USG desires the ability to …"'
            )
        return v


class ScenarioOut(ScenarioIn):
    """GET /programs/{id}/scenarios list item"""
    id: int
    program_id: int
    word_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScenariosBulkIn(BaseModel):
    """PUT /programs/{id}/scenarios — replaces all scenarios atomically"""
    scenarios: List[ScenarioIn]


# ─────────────────────────────────────────────────────────────────────────────
# Standards
# ─────────────────────────────────────────────────────────────────────────────

class StandardIn(BaseModel):
    """Single standard (used inside StandardsBulkIn). Each row is one (module, standard) pair."""
    standard_name: str
    module_name: Optional[str] = None
    applies_to_modules: bool = True
    catalog_id: Optional[str] = None
    notes: Optional[str] = None


class StandardOut(StandardIn):
    """GET /programs/{id}/standards list item"""
    id: int
    program_id: int
    applies: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class StandardsBulkIn(BaseModel):
    """PUT /programs/{id}/standards — replaces all standards atomically"""
    standards: List[StandardIn]


# ─────────────────────────────────────────────────────────────────────────────
# Sufficiency
# ─────────────────────────────────────────────────────────────────────────────

class GateResultOut(BaseModel):
    gate_id: str
    passed: bool
    message: str


class FieldCoverageOut(BaseModel):
    field_id: str
    label: str
    weight: float
    present: bool
    source: str      # "brief" | "program" | "module" | "wizard" | "standard" | "file"


class RuleViolationOut(BaseModel):
    rule_id: str
    severity: str    # "ERROR" | "WARN" | "INFO"
    message: str


class SufficiencyOut(BaseModel):
    """GET /programs/{id}/sufficiency"""
    level: str                                              # SufficiencyLevel value
    score: float                                            # 0–100
    gates: List[GateResultOut]
    coverage: List[FieldCoverageOut]
    missing_critical: List[str]                             # labels of missing weight ≥ 8
    warnings: List[str]                                     # labels of missing weight 4–7
    mig_id: Optional[str] = None                           # from rules engine
    modifiers: List[str] = Field(default_factory=list)     # DocModifier values
    rule_violations: List[RuleViolationOut] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Files
# ─────────────────────────────────────────────────────────────────────────────

class FileOut(BaseModel):
    """GET /programs/{id}/files list item"""
    id: int
    program_id: int
    filename: str
    relative_path: str
    size_bytes: int
    uploaded_at: datetime
    extracted_text: Optional[str] = None
    source_type: str = "program_input"

    model_config = {"from_attributes": True}


class ExtractionOut(BaseModel):
    """POST /programs/{id}/files/{fid}/extract response"""
    file_id: int
    filename: str
    chars_extracted: int
    chunks_created: int
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Document Generation
# ─────────────────────────────────────────────────────────────────────────────

class GenerateDocIn(BaseModel):
    """POST /programs/{id}/documents/generate"""
    doc_type: DocType
    force: bool = False    # regenerate even if current doc exists


class RegenerateSectionIn(BaseModel):
    """POST /programs/{id}/documents/{doc_id}/sections/regenerate"""
    section_name: str      # exact SectionDef.name, e.g. "MOSA & Data Rights"


class RegenerateSectionOut(BaseModel):
    """Response from per-section regeneration"""
    document_id: int
    section_name: str
    status: str            # "done" | "error"
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Tracking
# ─────────────────────────────────────────────────────────────────────────────

class AssumptionOut(BaseModel):
    field: str      # output field where the assumption appears
    text: str       # assumption text (contents of [ASSUMPTION: ...])


class EvidenceOut(BaseModel):
    source_type: str    # "structured_input" | "wizard_answer" | "file_chunk"
    key: str
    label: str


class SectionTrackingOut(BaseModel):
    section_name: str
    assumptions: List[AssumptionOut]
    evidence: List[EvidenceOut]
    assumption_count: int
    evidence_count: int


class DocumentTrackingOut(BaseModel):
    """GET /programs/{id}/documents/{doc_id}/tracking"""
    document_id: int
    doc_type: str
    sections: List[SectionTrackingOut]
    total_assumptions: int


class GenerateDocOut(BaseModel):
    """POST /programs/{id}/documents/generate response (async job)"""
    job_id: str
    status: str            # GenerationStatus value
    doc_type: str
    program_id: int
    document_id: Optional[int] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


class DocumentOut(BaseModel):
    """List item in GET /programs/{id}/documents"""
    id: int
    program_id: int
    doc_type: str
    file_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Wizard
# ─────────────────────────────────────────────────────────────────────────────

class WizardQuestionOut(BaseModel):
    id: str
    prompt: str
    help: str
    type: str
    options: Optional[List[Dict[str, Any]]] = None
    missing: bool


class WizardOut(BaseModel):
    """GET /programs/{id}/wizard"""
    questions: List[WizardQuestionOut]
    answers: Dict[str, Any]
    answered_count: int
    total_count: int
    percent_complete: float


class WizardAnswersIn(BaseModel):
    """PUT /programs/{id}/wizard"""
    answers: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compat aliases
# Import these in old routers that haven't been migrated yet.
# ─────────────────────────────────────────────────────────────────────────────

# Program
ProgramCreateV2  = ProgramIn
ProgramUpdateV2  = ProgramPatch
ProgramOutV2     = ProgramOut

# Brief
ProgramBriefInV2  = BriefIn
ProgramBriefOutV2 = BriefOut

# Module
ModuleInV2  = ModuleIn
ModuleOutV2 = ModuleOut

# Scenarios
MosaScenarioIn  = ScenarioIn
MosaScenarioOut = ScenarioOut

# Standards
ProgramStandardIn  = StandardIn
ProgramStandardOut = StandardOut

# Generation
GenerateDocRequestV2 = GenerateDocIn

# Extraction
ExtractionResultOut = ExtractionOut

# Wizard
QuestionOut        = WizardQuestionOut
WizardAnswersSaveIn = WizardAnswersIn

# File
ProgramFileOut = FileOut

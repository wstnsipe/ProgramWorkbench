from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel


class ProgramCreate(BaseModel):
    name: str


class ProgramOut(BaseModel):
    id: int
    name: str
    service_branch: Optional[str] = None
    army_pae: Optional[str] = None
    army_branch: Optional[str] = None
    mig_id: Optional[str] = None

    class Config:
        from_attributes = True


class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    service_branch: Optional[str] = None
    army_pae: Optional[str] = None
    army_branch: Optional[str] = None


class ProgramBriefIn(BaseModel):
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


class ProgramBriefOut(ProgramBriefIn):
    program_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class ProgramFileOut(BaseModel):
    id: int
    program_id: int
    filename: str
    relative_path: str
    size_bytes: int
    uploaded_at: datetime
    extracted_text: Optional[str] = None
    source_type: str = "program_input"

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: str
    prompt: str
    help: str
    type: str
    options: Optional[List[Dict[str, Any]]] = None
    missing: bool


class WizardOut(BaseModel):
    questions: List[QuestionOut]
    answers: Dict[str, Any]  # str for text answers; list of dicts for "modules" key
    answered_count: int
    total_count: int
    percent_complete: float


class ModuleWizardItem(BaseModel):
    """Structured module entry submitted from the wizard modules builder."""
    name: str
    description: Optional[str] = None
    rationale: Optional[str] = None
    interfaces: Optional[str] = None


class WizardAnswersIn(BaseModel):
    answers: Dict[str, Any]  # values are str for text questions, list[dict] for "modules" key


class ModuleIn(BaseModel):
    name: str
    description: Optional[str] = None
    rationale: Optional[str] = None
    key_interfaces: Optional[str] = None
    standards: Optional[str] = None
    tech_risk: bool = False
    obsolescence_risk: bool = False
    cots_candidate: bool = False


class ModuleOut(ModuleIn):
    id: int
    program_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FileTextOut(BaseModel):
    id: int
    file_id: int
    extracted_text: str
    meta_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FileChunkOut(BaseModel):
    id: int
    file_id: int
    chunk_index: int
    chunk_text: str
    meta_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeFileSummary(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    text_available: bool
    text_preview_500chars: Optional[str] = None
    source_type: str = "program_input"


class KnowledgeStats(BaseModel):
    file_count: int
    text_file_count: int


class KnowledgeSummaryOut(BaseModel):
    program: ProgramOut
    brief: Optional[ProgramBriefOut] = None
    wizard_answers: Dict[str, Optional[str]]
    modules: List[ModuleOut]
    program_files: List[KnowledgeFileSummary]
    exemplar_files: List[KnowledgeFileSummary]
    stats: KnowledgeStats


class GenerateDocRequest(BaseModel):
    doc_types: List[str]


class DocumentOut(BaseModel):
    id: int
    program_id: int
    doc_type: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReextractFileResult(BaseModel):
    file_id: int
    filename: str
    chars: int
    error: Optional[str] = None


class ReextractOut(BaseModel):
    reextracted: int
    files: List[ReextractFileResult]


class KnowledgeSearchResult(BaseModel):
    file_id: int
    filename: str
    match_count: int
    snippet: str


# ---------------------------------------------------------------------------
# Context build output schema
# ---------------------------------------------------------------------------


class ContextBuildOut(BaseModel):
    program_id: int
    summary: str
    missing_info_questions: List[str]
    context_path: str


class KnowledgeIndexOut(BaseModel):
    program_id: int
    chunks_indexed: int
    files_indexed: int


class KnowledgeTopFile(BaseModel):
    file_id: int
    filename: str
    chunk_count: int


class KnowledgeStatusOut(BaseModel):
    program_id: int
    file_count: int
    text_file_count: int
    chunk_count: int
    last_indexed_at: Optional[datetime] = None
    top_files: List[KnowledgeTopFile]


# ---------------------------------------------------------------------------
# Smart RFI structured-output schema
# ---------------------------------------------------------------------------


class ModuleTableRow(BaseModel):
    module_name: str
    rationale: str
    key_interfaces: str
    standards: str
    tech_risk: str
    obsolescence_risk: str
    cots_candidate: str


class RfiSourceItem(BaseModel):
    file_id: int
    filename: str
    excerpt: str


class RfiPlan(BaseModel):
    overview: str
    rfi_purpose: str
    program_context: str
    mosa_requirements: List[str]
    questions_to_industry: List[str]
    requested_deliverables: List[str]
    submission_instructions: List[str]
    module_table_rows: List[ModuleTableRow]
    sources_used: List[RfiSourceItem]
    citations: Dict[str, List[int]] = {}


# ---------------------------------------------------------------------------
# Smart MOSA Conformance Plan structured-output schema
# (mirrors llm/mosa_schema.py – kept here for FastAPI response_model use)
# ---------------------------------------------------------------------------

# Re-export the canonical Pydantic models from the llm module so main.py
# can import a single flat namespace.
from llm.mosa_schema import (  # noqa: E402
    MosaModuleConformance,
    MosaInterface,
    MosaRisk,
    MosaVerificationMilestone,
    MosaAssessmentCriterion,
    MosaScenario,
    MosaSourceItem as MosaSourceItem,
    MosaPlan,
)


# ---------------------------------------------------------------------------
# Smart Acquisition Strategy structured-output schema
# ---------------------------------------------------------------------------


class AcqStrategyTitleBlock(BaseModel):
    program_name: str
    date: str
    organization: str


class AcqMilestone(BaseModel):
    name: str
    date: str
    description: str


class AcqCostEstimates(BaseModel):
    development: str
    production_unit: str
    sustainment_annual: str


class AcqRisk(BaseModel):
    risk_id: str
    description: str
    probability: str  # "Low" / "Medium" / "High"
    impact: str       # "Low" / "Medium" / "High"
    mitigation: str
    owner: str


class AcqStandardRef(BaseModel):
    name: str
    description: str


class AcqModuleRow(BaseModel):
    module_name: str
    rationale: str
    key_interfaces: str
    standards: str
    tech_risk: str
    obsolescence_risk: str
    cots_candidate: str


class AcqStrategySourceItem(BaseModel):
    file_id: int
    filename: str
    excerpt: str


class AcqStrategyPlan(BaseModel):
    title_block: AcqStrategyTitleBlock
    executive_summary: str
    acquisition_approach: str
    schedule_milestones: List[AcqMilestone]
    cost_estimates: AcqCostEstimates
    risk_register: List[AcqRisk]
    standards_references: List[AcqStandardRef]
    mosa_approach: str
    mosa_bullets: List[str]
    data_rights_approach: str
    test_verification_approach: str
    contracting_strategy: str
    module_table_rows: List[AcqModuleRow]
    sources_used: List[AcqStrategySourceItem]
    citations: Dict[str, List[int]] = {}


# ---------------------------------------------------------------------------
# Smart SEP structured-output schema
# ---------------------------------------------------------------------------

from llm.sep_schema import (  # noqa: E402
    SepTitleBlock,
    SepTechReview,
    SepRequirementsTraceability,
    SepArchitectureMosa,
    SepRisk,
    SepConfigMgmt,
    SepVnV,
    SepDataMgmt,
    SepSpecialtyEng,
    SepGlossaryEntry,
    SepAppendices,
    SepSourceItem as SepSourceItem,
    SepPlan,
)

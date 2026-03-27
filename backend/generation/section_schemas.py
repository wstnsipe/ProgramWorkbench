"""
Per-section Pydantic output schemas for section-by-section document generation.

Each section gets its own focused schema — not the full document schema.
The full document schemas (RfiPlan, AcqStrategyPlan, etc.) are still used for
final assembly validation.
"""
from typing import List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

class SourceCitation(BaseModel):
    file_id: int
    filename: str
    excerpt: str


# ---------------------------------------------------------------------------
# RFI sections
# ---------------------------------------------------------------------------

class RfiOverviewSection(BaseModel):
    overview: str
    rfi_purpose: str
    program_context: str


class RfiMosaSection(BaseModel):
    mosa_requirements: List[str]


class RfiQuestionsSection(BaseModel):
    questions_to_industry: List[str]


class RfiDeliverablesSection(BaseModel):
    requested_deliverables: List[str]
    submission_instructions: List[str]


# ---------------------------------------------------------------------------
# Acquisition Strategy sections
# ---------------------------------------------------------------------------

class AcqExecSummarySection(BaseModel):
    executive_summary: str
    acquisition_approach: str


class Milestone(BaseModel):
    name: str
    month_offset: int       # months from program start
    description: str
    compression_rationale: Optional[str] = None   # set when TIMELINE_SHORT active


class AcqScheduleSection(BaseModel):
    milestones: List[Milestone]


class AcqCostSection(BaseModel):
    development: str
    production_unit: str
    sustainment_annual: str


class Risk(BaseModel):
    title: str
    probability: str        # H | M | L
    impact: str             # H | M | L
    mitigation: str
    owner: str              # PMO | Contractor | Government


class AcqRiskSection(BaseModel):
    risks: List[Risk]


class ModuleSustainabilityEntry(BaseModel):
    module_name: str
    scenario_type: str                  # reprocure | reuse | recompete
    competition_rationale: str          # how this scenario enables competition or independence
    interface_standards: List[str]      # standards governing this module's boundary
    data_rights_required: str           # e.g. "Government Purpose Rights", "Unlimited Rights"


class AcqMosaSection(BaseModel):
    mosa_approach: str                              # 1–2 paragraph narrative
    module_sustainability: List[ModuleSustainabilityEntry]  # one entry per module
    data_rights_approach: str                       # program-wide data rights strategy


class AcqContractingSection(BaseModel):
    contracting_vehicle: str
    competition_strategy: str
    commercial_rationale: Optional[str] = None   # populated when EMPHASIZE_COMMERCIAL active


# ---------------------------------------------------------------------------
# SEP sections
# ---------------------------------------------------------------------------

class TechReview(BaseModel):
    name: str               # e.g. SRR, PDR, CDR, TRR
    month_offset: int       # months from program start
    entry_criteria: str
    exit_criteria: str


class SepTechSection(BaseModel):
    tech_review_schedule: List[TechReview]
    requirements_traceability_approach: str


class ModuleBoundary(BaseModel):
    module_name: str
    boundary_description: str           # what crosses this boundary (data, control, power, RF, etc.)
    interface_standard: str             # governing standard (e.g. SOSA, SCA 4.1, MIL-STD-1553)
    enables: str                        # what the standard boundary enables (recompete, upgrade, substitution)
    hw_sw_separation_note: Optional[str] = None  # populated when HW_SW_SEPARATION modifier active


class SepArchSection(BaseModel):
    architecture_description: str
    module_boundaries: List[ModuleBoundary]     # replaces flat interface_standards list
    mosa_compliance: str


class SepRiskSection(BaseModel):
    risks: List[Risk]       # reuses Risk from AcqRiskSection


class SepVnVSection(BaseModel):
    verification_approach: str
    validation_approach: str
    test_levels: List[str]


# ---------------------------------------------------------------------------
# MCP sections
# ---------------------------------------------------------------------------

class McpOverviewSection(BaseModel):
    overview: str
    conformance_objectives: List[str]


class McpModuleAssessment(BaseModel):
    module_name: str
    scenario_type: str                  # reprocure | reuse | recompete
    competition_enablement: str         # whether current interface docs support recompete; gaps if not
    interface_compliance: str           # compliance status against applicable standards
    risks: List[str]                    # module-specific MOSA risks
    verification_approach: str          # how conformance will be verified


class McpModuleSection(BaseModel):
    module_assessments: List[McpModuleAssessment]


class VerificationMilestone(BaseModel):
    name: str
    month_offset: int
    method: str             # analysis | inspection | demonstration | test
    success_criteria: str


class AssessmentCriterion(BaseModel):
    criterion: str
    pass_threshold: str
    assessment_method: str


class McpVerificationSection(BaseModel):
    milestones: List[VerificationMilestone]
    assessment_criteria: List[AssessmentCriterion]

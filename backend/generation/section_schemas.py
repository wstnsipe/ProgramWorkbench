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


class AcqScheduleSection(BaseModel):
    milestones: List[dict]   # [{name, date, description}]


class AcqCostSection(BaseModel):
    development: str
    production_unit: str
    sustainment_annual: str


class AcqRiskSection(BaseModel):
    risks: List[dict]   # [{risk_id, description, probability, impact, mitigation, owner}]


class AcqMosaSection(BaseModel):
    mosa_approach: str
    mosa_bullets: List[str]
    data_rights_approach: str


class AcqContractingSection(BaseModel):
    contracting_strategy: str
    test_verification_approach: str


# ---------------------------------------------------------------------------
# SEP sections
# ---------------------------------------------------------------------------

class SepTechSection(BaseModel):
    tech_review_schedule: List[dict]
    requirements_traceability_approach: str


class SepArchSection(BaseModel):
    architecture_description: str
    mosa_compliance: str
    interface_standards: List[str]


class SepRiskSection(BaseModel):
    risks: List[dict]


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


class McpModuleSection(BaseModel):
    module_assessments: List[dict]  # [{module_name, interfaces, risks, verification}]


class McpVerificationSection(BaseModel):
    milestones: List[dict]
    assessment_criteria: List[dict]

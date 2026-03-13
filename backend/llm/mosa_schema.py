"""Pydantic schema and LLM prompt template for Smart MOSA Conformance Plan."""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class MosaModuleConformance(BaseModel):
    module_name: str
    open_standards: str
    interface_type: str          # "HW" / "SW" / "Data" / "HW/SW"
    data_rights_category: str    # "Unlimited Rights" / "Government Purpose Rights" / etc.
    conformance_status: str      # "Compliant" / "Partial" / "TBD"
    verification_method: str
    notes: str


class MosaInterface(BaseModel):
    interface_name: str
    interface_type: str   # "HW" / "SW" / "Data"
    standard: str
    owner: str            # "Government" / "Contractor" / "TBD"
    status: str           # "Defined" / "TBD"


class MosaRisk(BaseModel):
    risk_area: str
    description: str
    likelihood: str   # "Low" / "Medium" / "High"
    impact: str       # "Low" / "Medium" / "High"
    mitigation: str


class MosaVerificationMilestone(BaseModel):
    milestone: str
    evidence_required: str
    responsible_party: str
    completion_criteria: str


class MosaAssessmentCriterion(BaseModel):
    criterion: str
    status: str          # "Compliant" / "Partial" / "Non-Compliant" / "TBD"
    evidence: str
    gap_description: str


class MosaScenario(BaseModel):
    scenario_title: str
    affected_modules: str
    approach: str
    applicable_standards: str


class MosaSourceItem(BaseModel):
    chunk_id: int
    source_filename: str
    excerpt: str


# ---------------------------------------------------------------------------
# Top-level plan
# ---------------------------------------------------------------------------


class MosaPlan(BaseModel):
    executive_summary: str
    program_context: str
    mosa_objectives: List[str]
    tailoring_rationale: str
    module_inventory: List[MosaModuleConformance]
    interface_registry: List[MosaInterface]
    standards_mapping: List[str]
    data_rights_posture: str
    verification_milestones: List[MosaVerificationMilestone]
    risk_register: List[MosaRisk]
    assessment_matrix: List[MosaAssessmentCriterion]
    mosa_scenarios: List[MosaScenario]
    sources_used: List[MosaSourceItem]
    citations: Dict[str, List[int]] = {}


# ---------------------------------------------------------------------------
# LLM JSON schema string (injected into system prompt)
# ---------------------------------------------------------------------------

MOSA_PLAN_JSON_SCHEMA = """\
Return ONLY a JSON object with exactly these keys (no extra keys, no markdown fences):
{
  "executive_summary": "<string: 2-4 sentence summary of the MOSA Conformance Plan and its purpose>",
  "program_context": "<string: detailed program context and background, 2-5 paragraphs>",
  "mosa_objectives": ["<string>", ...],
  "tailoring_rationale": "<string: explanation of how MOSA requirements are tailored to this program's characteristics>",
  "module_inventory": [
    {
      "module_name": "<string>",
      "open_standards": "<string: applicable open standards>",
      "interface_type": "<HW|SW|Data|HW/SW>",
      "data_rights_category": "<Unlimited Rights|Government Purpose Rights|Limited Rights|TBD>",
      "conformance_status": "<Compliant|Partial|TBD>",
      "verification_method": "<string: how conformance will be verified>",
      "notes": "<string>"
    }
  ],
  "interface_registry": [
    {
      "interface_name": "<string>",
      "interface_type": "<HW|SW|Data>",
      "standard": "<string>",
      "owner": "<Government|Contractor|TBD>",
      "status": "<Defined|TBD>"
    }
  ],
  "standards_mapping": ["<string: 'Module → Standard' or program-level standard statement>", ...],
  "data_rights_posture": "<string: 2-4 paragraph description of the program's technical data and data rights strategy>",
  "verification_milestones": [
    {
      "milestone": "<string: e.g. PDR, CDR, IOT&E>",
      "evidence_required": "<string>",
      "responsible_party": "<string>",
      "completion_criteria": "<string>"
    }
  ],
  "risk_register": [
    {
      "risk_area": "<string>",
      "description": "<string>",
      "likelihood": "<Low|Medium|High>",
      "impact": "<Low|Medium|High>",
      "mitigation": "<string>"
    }
  ],
  "assessment_matrix": [
    {
      "criterion": "<string: MOSA assessment criterion>",
      "status": "<Compliant|Partial|Non-Compliant|TBD>",
      "evidence": "<string: evidence or artifact supporting this status>",
      "gap_description": "<string: gap to be closed, or 'None' if compliant>"
    }
  ],
  "mosa_scenarios": [
    {
      "scenario_title": "<string>",
      "affected_modules": "<string>",
      "approach": "<string>",
      "applicable_standards": "<string>"
    }
  ],
  "sources_used": [
    {
      "chunk_id": <integer>,
      "source_filename": "<string>",
      "excerpt": "<string: 1-2 sentence excerpt from the chunk>"
    }
  ],
  "citations": {
    "<section_key e.g. executive_summary>": [<source_number_integer>, ...]
  }
}
"""

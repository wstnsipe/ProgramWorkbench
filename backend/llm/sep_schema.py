"""Pydantic schema and LLM prompt template for Smart SEP (Systems Engineering Plan)."""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class SepTitleBlock(BaseModel):
    program_name: str
    organization: str
    date: str
    version: str


class SepTechReview(BaseModel):
    name: str
    purpose: str
    entry_criteria: str
    exit_criteria: str
    artifacts: List[str]


class SepRequirementsTraceability(BaseModel):
    approach: str
    tools: str
    digital_thread_notes: str


class SepArchitectureMosa(BaseModel):
    mosa_approach: str
    modules_summary: str
    interfaces_summary: str
    standards_summary: str


class SepRisk(BaseModel):
    risk: str
    cause: str
    likelihood: str   # "Low" / "Medium" / "High"
    impact: str       # "Low" / "Medium" / "High"
    mitigation: str
    owner: str


class SepConfigMgmt(BaseModel):
    approach: str
    baselines: List[str]
    change_control: str


class SepVnV(BaseModel):
    strategy: str
    test_levels: List[str]
    acceptance_criteria: str


class SepDataMgmt(BaseModel):
    data_items: List[str]
    data_rights_strategy: str
    repo_notes: str


class SepSpecialtyEng(BaseModel):
    cyber: str
    safety: str
    airworthiness: str
    human_factors: str
    reliability: str
    maintainability: str


class SepGlossaryEntry(BaseModel):
    term: str
    definition: str


class SepAppendices(BaseModel):
    glossary: List[SepGlossaryEntry]
    references: List[str]


class SepSourceItem(BaseModel):
    file_id: int
    filename: str
    excerpt: str


# ---------------------------------------------------------------------------
# Top-level plan
# ---------------------------------------------------------------------------


class SepPlan(BaseModel):
    title_block: SepTitleBlock
    executive_summary: str
    program_overview: str
    se_strategy: str
    tech_reviews: List[SepTechReview]
    requirements_traceability: SepRequirementsTraceability
    architecture_mosa: SepArchitectureMosa
    risk_register: List[SepRisk]
    config_mgmt: SepConfigMgmt
    vnv: SepVnV
    data_mgmt: SepDataMgmt
    specialty_eng: SepSpecialtyEng
    appendices: SepAppendices
    sources_used: List[SepSourceItem]
    citations: Dict[str, List[int]] = {}


# ---------------------------------------------------------------------------
# LLM JSON schema string (injected into system prompt)
# ---------------------------------------------------------------------------

SEP_PLAN_JSON_SCHEMA = """\
Return ONLY a JSON object with exactly these keys (no extra keys, no markdown fences):
{
  "title_block": {
    "program_name": "<string>",
    "organization": "<string: e.g. 'Program Executive Office Aviation'>",
    "date": "<string: e.g. 'February 2026'>",
    "version": "<string: e.g. '1.0'>"
  },
  "executive_summary": "<string: 2-4 paragraph summary of the SEP, its purpose, and program context>",
  "program_overview": "<string: 2-4 paragraph description of the program, its mission, technical approach, and acquisition phase>",
  "se_strategy": "<string: 2-4 paragraphs describing the overall systems engineering approach, SE process model, and key SE activities>",
  "tech_reviews": [
    {
      "name": "<string: e.g. 'System Requirements Review (SRR)'>",
      "purpose": "<string>",
      "entry_criteria": "<string>",
      "exit_criteria": "<string>",
      "artifacts": ["<string>", ...]
    }
  ],
  "requirements_traceability": {
    "approach": "<string: description of requirements management approach and traceability methodology>",
    "tools": "<string: list of tools used, e.g. DOORS, Jira, Excel>",
    "digital_thread_notes": "<string: how the digital thread supports requirements traceability>"
  },
  "architecture_mosa": {
    "mosa_approach": "<string: description of MOSA strategy for this program>",
    "modules_summary": "<string: summary of defined modules and decomposition rationale>",
    "interfaces_summary": "<string: summary of key interfaces and interface control strategy>",
    "standards_summary": "<string: applicable open standards and mapping to modules>"
  },
  "risk_register": [
    {
      "risk": "<string: risk title>",
      "cause": "<string: root cause>",
      "likelihood": "<Low|Medium|High>",
      "impact": "<Low|Medium|High>",
      "mitigation": "<string: mitigation strategy>",
      "owner": "<string: responsible party>"
    }
  ],
  "config_mgmt": {
    "approach": "<string: configuration management approach and CM plan summary>",
    "baselines": ["<string: e.g. 'Functional Baseline (FBL) at SRR'>", ...],
    "change_control": "<string: description of the Engineering Change Proposal (ECP) and change control process>"
  },
  "vnv": {
    "strategy": "<string: 2-3 paragraph verification and validation strategy>",
    "test_levels": ["<string: e.g. 'Unit Testing'>", ...],
    "acceptance_criteria": "<string: description of acceptance criteria and success metrics>"
  },
  "data_mgmt": {
    "data_items": ["<string: CDRL or data item, e.g. 'DI-SESS-81785 Systems Engineering Plan'>", ...],
    "data_rights_strategy": "<string: description of technical data rights posture and government data rights>",
    "repo_notes": "<string: notes on data repositories, digital engineering environment, or data management tools>"
  },
  "specialty_eng": {
    "cyber": "<string: cybersecurity / RMF approach for this program>",
    "safety": "<string: system safety approach and applicable standards>",
    "airworthiness": "<string: airworthiness certification approach and authority coordination, or 'Not applicable' if irrelevant>",
    "human_factors": "<string: human systems integration (HSI) and human factors engineering approach>",
    "reliability": "<string: reliability engineering approach, RAMs analysis, and key reliability requirements>",
    "maintainability": "<string: maintainability engineering approach and supportability considerations>"
  },
  "appendices": {
    "glossary": [
      {"term": "<string>", "definition": "<string>"}
    ],
    "references": ["<string: full document reference, e.g. 'DoDI 5000.02, Operation of the Adaptive Acquisition Framework'>", ...]
  },
  "sources_used": [
    {
      "file_id": <integer: ID of the uploaded program file>,
      "filename": "<string>",
      "excerpt": "<string: 1-2 sentence excerpt from the file supporting this plan>"
    }
  ],
  "citations": {
    "<section_key e.g. executive_summary>": [<source_number_integer>, ...]
  }
}
"""

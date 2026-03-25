"""
orchestrator.py — Drives section-by-section document generation.

Flow per document:
  1. Load program context (brief, modules, wizard answers, standards)
  2. Run rules engine → get modifiers
  3. For each section in TEMPLATE_REGISTRY[doc_type].section_order:
     a. Assemble section-specific fact pack
     b. Hybrid-search relevant chunks (facts track + style track)
     c. Retrieve exemplar style excerpt if available
     d. Call section_generator.generate_section()
     e. Accumulate section outputs
  4. Assemble full document dict and validate against master schema
  5. Hand off to renderer (docx_builder wrapper)
  6. Persist ProgramDocument record, return download path
"""
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

import models
from rules import evaluate_rules, RulesInput
from services.sufficiency_service import compute_sufficiency
from generation.section_generator import generate_section
from generation.section_schemas import (
    # RFI
    RfiOverviewSection, RfiMosaSection, RfiQuestionsSection, RfiDeliverablesSection,
    # Acq Strategy
    AcqExecSummarySection, AcqScheduleSection, AcqCostSection,
    AcqRiskSection, AcqMosaSection, AcqContractingSection,
    # SEP
    SepTechSection, SepArchSection, SepRiskSection, SepVnVSection,
    # MCP
    McpOverviewSection, McpModuleSection, McpVerificationSection,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Section definitions per doc_type
# ---------------------------------------------------------------------------

@dataclass
class SectionDef:
    name: str                   # human-readable section name
    schema_class: type          # Pydantic output schema
    instructions: str           # ≤25-line system prompt instructions for this section
    fact_keys: list[str]        # keys from full fact pack to include
    exemplar_pattern: str       # heading keyword to match in exemplar


_RFI_SECTIONS: list[SectionDef] = [
    SectionDef(
        name="Overview & Purpose",
        schema_class=RfiOverviewSection,
        instructions="Write a concise overview of the RFI, its purpose, and program context. 2–4 paragraphs.",
        fact_keys=["program_name", "program_description", "service_branch", "dev_cost_estimate"],
        exemplar_pattern="overview",
    ),
    SectionDef(
        name="MOSA Requirements",
        schema_class=RfiMosaSection,
        instructions="List specific MOSA requirements for this program as bullet points. Reference MIG if known.",
        fact_keys=["modules", "mig_id", "modifiers", "standards"],
        exemplar_pattern="mosa",
    ),
    SectionDef(
        name="Questions to Industry",
        schema_class=RfiQuestionsSection,
        instructions="Generate 8–12 specific questions to industry. Ground in program modules and MOSA requirements.",
        fact_keys=["program_description", "modules", "standards", "scenarios"],
        exemplar_pattern="question",
    ),
    SectionDef(
        name="Deliverables & Submission",
        schema_class=RfiDeliverablesSection,
        instructions="List required deliverables and standard DoD submission instructions.",
        fact_keys=["service_branch", "timeline_months"],
        exemplar_pattern="deliverable",
    ),
]

_ACQ_STRATEGY_SECTIONS: list[SectionDef] = [
    SectionDef(
        name="Executive Summary",
        schema_class=AcqExecSummarySection,
        instructions="Write executive summary (3–5 sentences) and acquisition approach (1–2 paragraphs).",
        fact_keys=["program_name", "program_description", "service_branch", "dev_cost_estimate", "timeline_months"],
        exemplar_pattern="executive summary",
    ),
    SectionDef(
        name="Schedule & Milestones",
        schema_class=AcqScheduleSection,
        instructions="Generate 4–8 acquisition milestones. Use timeline_months to space them. Include MS B, MS C, IOC.",
        fact_keys=["timeline_months", "program_description", "attritable"],
        exemplar_pattern="milestone",
    ),
    SectionDef(
        name="Cost Estimates",
        schema_class=AcqCostSection,
        instructions="Format cost estimates as narrative strings. If values unknown, use [ASSUMPTION: ...].",
        fact_keys=["dev_cost_estimate", "production_unit_cost"],
        exemplar_pattern="cost",
    ),
    SectionDef(
        name="Risk Register",
        schema_class=AcqRiskSection,
        instructions="Generate 4–6 acquisition risks with probability/impact/mitigation. Ground in tech_risk and module flags.",
        fact_keys=["modules", "modifiers", "mission_critical", "safety_critical"],
        exemplar_pattern="risk",
    ),
    SectionDef(
        name="MOSA & Data Rights",
        schema_class=AcqMosaSection,
        instructions="Describe MOSA approach, list 5+ MOSA bullets, and explain data rights strategy.",
        fact_keys=["modules", "mig_id", "standards", "modifiers", "scenarios"],
        exemplar_pattern="mosa",
    ),
    SectionDef(
        name="Contracting Strategy",
        schema_class=AcqContractingSection,
        instructions="Describe contracting vehicle, competition strategy, and test/verification approach.",
        fact_keys=["dev_cost_estimate", "attritable", "cots_count", "service_branch"],
        exemplar_pattern="contract",
    ),
]

_SEP_SECTIONS: list[SectionDef] = [
    SectionDef(
        name="Technical Reviews & Requirements",
        schema_class=SepTechSection,
        instructions="List technical review schedule (SRR, PDR, CDR, etc.) and describe requirements traceability approach.",
        fact_keys=["timeline_months", "mission_critical", "safety_critical", "program_description"],
        exemplar_pattern="technical review",
    ),
    SectionDef(
        name="Architecture & MOSA",
        schema_class=SepArchSection,
        instructions="Describe system architecture, MOSA compliance approach, and interface standards used.",
        fact_keys=["modules", "standards", "mig_id", "modifiers"],
        exemplar_pattern="architecture",
    ),
    SectionDef(
        name="Risk Management",
        schema_class=SepRiskSection,
        instructions="Generate 4–6 systems engineering risks with mitigations.",
        fact_keys=["modules", "modifiers", "safety_critical"],
        exemplar_pattern="risk",
    ),
    SectionDef(
        name="Verification & Validation",
        schema_class=SepVnVSection,
        instructions="Describe V&V approach, including DO-178 if applicable. List test levels.",
        fact_keys=["modifiers", "safety_critical", "mission_critical", "software_large_part"],
        exemplar_pattern="verification",
    ),
]

_MCP_SECTIONS: list[SectionDef] = [
    SectionDef(
        name="Conformance Overview",
        schema_class=McpOverviewSection,
        instructions="Write MOSA conformance plan overview and list 4–6 conformance objectives.",
        fact_keys=["program_name", "program_description", "mig_id", "modules"],
        exemplar_pattern="overview",
    ),
    SectionDef(
        name="Module Assessments",
        schema_class=McpModuleSection,
        instructions="For each module, assess interface compliance, risks, and verification approach.",
        fact_keys=["modules", "standards", "modifiers"],
        exemplar_pattern="module",
    ),
    SectionDef(
        name="Verification Milestones",
        schema_class=McpVerificationSection,
        instructions="Define conformance verification milestones and assessment criteria.",
        fact_keys=["timeline_months", "mission_critical", "modules"],
        exemplar_pattern="verification",
    ),
]

SECTION_MAP: dict[str, list[SectionDef]] = {
    "rfi":          _RFI_SECTIONS,
    "acq_strategy": _ACQ_STRATEGY_SECTIONS,
    "sep":          _SEP_SECTIONS,
    "mcp":          _MCP_SECTIONS,
}


# ---------------------------------------------------------------------------
# Fact pack assembly
# ---------------------------------------------------------------------------

def _build_full_fact_pack(
    program: Any,
    brief: Optional[Any],
    modules: list,
    wizard_answers: dict,
    standards: list,
    rules_result: Any,
) -> dict[str, Any]:
    """Assemble all available program facts into a flat dict."""
    brief_d = brief.__dict__ if brief else {}
    module_list = [
        {
            "name": m.name,
            "description": m.description,
            "rationale": m.rationale,
            "key_interfaces": m.key_interfaces,
            "standards": m.standards,
            "tech_risk": m.tech_risk,
            "obsolescence_risk": m.obsolescence_risk,
            "cots_candidate": m.cots_candidate,
        }
        for m in modules
    ]
    standard_list = [
        {"name": s.standard_name, "applies": s.applies, "notes": s.notes}
        for s in standards
    ]

    scenarios_raw = wizard_answers.get("g_mosa_scenarios", "[]")
    try:
        scenarios = json.loads(scenarios_raw) if isinstance(scenarios_raw, str) else (scenarios_raw or [])
    except Exception:
        scenarios = []

    return {
        "program_name": program.name,
        "service_branch": getattr(program, "service_branch", None),
        "army_pae": getattr(program, "army_pae", None),
        "mig_id": rules_result.mig_id,
        "program_description": brief_d.get("program_description"),
        "dev_cost_estimate": brief_d.get("dev_cost_estimate"),
        "production_unit_cost": brief_d.get("production_unit_cost"),
        "timeline_months": brief_d.get("timeline_months"),
        "attritable": brief_d.get("attritable"),
        "sustainment_tail": brief_d.get("sustainment_tail"),
        "software_large_part": brief_d.get("software_large_part"),
        "mission_critical": brief_d.get("mission_critical"),
        "safety_critical": brief_d.get("safety_critical"),
        "similar_programs_exist": brief_d.get("similar_programs_exist"),
        "modules": module_list,
        "cots_count": sum(1 for m in module_list if m.get("cots_candidate")),
        "scenarios": scenarios,
        "standards": standard_list,
        "modifiers": [m.value for m in rules_result.modifiers],
        "wizard_answers": wizard_answers,
    }


def _slice_fact_pack(full: dict, keys: list[str]) -> dict:
    """Return only the keys this section needs."""
    return {k: full[k] for k in keys if k in full}


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def generate_document(
    *,
    db: Session,
    program_id: int,
    doc_type: str,
    output_path: str,
) -> dict[str, Any]:
    """
    Generate a complete document for program_id.
    Returns a dict of all assembled section outputs.

    Caller is responsible for:
      - Persisting a ProgramDocument record
      - Calling the renderer to write the .docx file
    """
    if doc_type not in SECTION_MAP:
        raise ValueError(f"Unknown doc_type: {doc_type}")

    # ---- Load data ----
    program = db.query(models.Program).filter_by(id=program_id).first()
    if not program:
        raise ValueError(f"Program {program_id} not found")

    brief = db.query(models.ProgramBrief).filter_by(program_id=program_id).first()
    modules = db.query(models.Module).filter_by(program_id=program_id).all()
    answers_rows = db.query(models.ProgramAnswer).filter_by(program_id=program_id).all()
    wizard_answers = {r.question_id: r.answer_text for r in answers_rows}

    # Load standards from new table (graceful fallback if table doesn't exist yet)
    try:
        from models_v2 import ProgramStandard
        standards = db.query(ProgramStandard).filter_by(program_id=program_id).all()
    except Exception:
        standards = []

    file_count = db.query(models.ProgramFile).filter_by(
        program_id=program_id, source_type="program_input"
    ).count()

    # ---- Run rules engine ----
    rules_inp = RulesInput(
        service_branch=getattr(program, "service_branch", None),
        army_pae=getattr(program, "army_pae", None),
        dev_cost_estimate=brief.dev_cost_estimate if brief else None,
        attritable=brief.attritable if brief else None,
        sustainment_tail=brief.sustainment_tail if brief else None,
        software_large_part=brief.software_large_part if brief else None,
        mission_critical=brief.mission_critical if brief else None,
        safety_critical=brief.safety_critical if brief else None,
        similar_programs_exist=getattr(brief, "similar_programs_exist", None) if brief else None,
        timeline_months=getattr(brief, "timeline_months", None) if brief else None,
        module_count=len(modules),
        modules_with_cots=sum(1 for m in modules if m.cots_candidate),
        modules_with_tech_risk=sum(1 for m in modules if m.tech_risk),
        modules_with_obsolescence_risk=sum(1 for m in modules if m.obsolescence_risk),
    )
    rules_result = evaluate_rules(rules_inp)

    # ---- Build fact pack ----
    full_facts = _build_full_fact_pack(
        program, brief, modules, wizard_answers, standards, rules_result
    )

    # ---- Generate sections ----
    section_defs = SECTION_MAP[doc_type]
    assembled: dict[str, Any] = {}

    for sec in section_defs:
        logger.info("Generating section '%s' for program %d (%s)", sec.name, program_id, doc_type)

        # Retrieve supporting chunks (hook into existing retrieval)
        chunks = _retrieve_chunks_for_section(db, program_id, sec, full_facts)

        # Retrieve exemplar style excerpt
        style_excerpt = _get_exemplar_style(db, program_id, doc_type, sec.exemplar_pattern)

        # Slice fact pack to only what this section needs
        fact_pack = _slice_fact_pack(full_facts, sec.fact_keys)

        section_output = generate_section(
            section_name=sec.name,
            section_instructions=sec.instructions,
            doc_type=doc_type,
            output_schema=sec.schema_class,
            fact_pack=fact_pack,
            retrieved_chunks=chunks,
            modifiers=[m.value for m in rules_result.modifiers],
            style_excerpt=style_excerpt,
            program_name=program.name,
        )
        assembled[sec.name] = section_output

    assembled["_meta"] = {
        "program_id": program_id,
        "doc_type": doc_type,
        "mig_id": rules_result.mig_id,
        "modifiers": [m.value for m in rules_result.modifiers],
    }

    return assembled


def _retrieve_chunks_for_section(
    db: Session,
    program_id: int,
    sec: SectionDef,
    full_facts: dict,
) -> list[str]:
    """
    Retrieve relevant chunks for a section using a simple keyword query.
    Replace with hybrid search once llm/retrieval.py is upgraded.
    """
    try:
        from llm.retrieval import retrieve_chunks_vector
        query = f"{sec.name} {full_facts.get('program_description', '')} {full_facts.get('program_name', '')}"
        results = retrieve_chunks_vector(db=db, program_id=program_id, query=query, top_k=6)
        return [r.chunk_text for r in results]
    except Exception as exc:
        logger.warning("Chunk retrieval failed for section '%s': %s", sec.name, exc)
        return []


def _get_exemplar_style(
    db: Session,
    program_id: int,
    doc_type: str,
    pattern: str,
) -> Optional[str]:
    """
    Fetch a cached exemplar style excerpt matching the section pattern.
    Falls back gracefully if ExemplarStyle table doesn't exist yet.
    """
    try:
        from models_v2 import ExemplarStyle
        row = (
            db.query(ExemplarStyle)
            .filter(ExemplarStyle.doc_type == doc_type)
            .filter(ExemplarStyle.section_name.ilike(f"%{pattern}%"))
            .first()
        )
        return row.style_excerpt if row else None
    except Exception:
        return None

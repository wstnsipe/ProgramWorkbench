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
from generation.tracking import track_section
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
        fact_keys=["program_name", "program_description", "service_branch", "dev_cost_estimate", "similar_programs"],
        exemplar_pattern="overview",
    ),
    SectionDef(
        name="MOSA Requirements",
        schema_class=RfiMosaSection,
        instructions="List specific MOSA requirements for this program as bullet points. Reference MIG if known.",
        fact_keys=["modules", "mig_id", "modifiers", "standards", "scenarios", "software_standards"],
        exemplar_pattern="mosa",
    ),
    SectionDef(
        name="Questions to Industry",
        schema_class=RfiQuestionsSection,
        instructions="Generate 8–12 specific questions to industry. Ground in program modules and MOSA requirements.",
        fact_keys=["program_description", "modules", "standards", "scenarios", "tech_challenges", "commercial_solutions"],
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
        fact_keys=["program_name", "program_description", "service_branch", "dev_cost_estimate", "timeline_months", "similar_programs"],
        exemplar_pattern="executive summary",
    ),
    SectionDef(
        name="Schedule & Milestones",
        schema_class=AcqScheduleSection,
        instructions="Generate 4–8 acquisition milestones. Use timeline_months to space them. Include MS B, MS C, IOC. If rule_violations contains TIMELINE_SHORT, include schedule compression rationale.",
        fact_keys=["timeline_months", "program_description", "attritable", "rule_violations"],
        exemplar_pattern="milestone",
    ),
    SectionDef(
        name="Cost Estimates",
        schema_class=AcqCostSection,
        instructions="Format cost estimates as narrative strings. If values unknown, use [ASSUMPTION: ...].",
        fact_keys=["dev_cost_estimate", "production_unit_cost", "recommended_module_count_min", "recommended_module_count_max"],
        exemplar_pattern="cost",
    ),
    SectionDef(
        name="Risk Register",
        schema_class=AcqRiskSection,
        instructions="Generate 4–6 acquisition risks with probability/impact/mitigation. Ground in module flags, tech_challenges, and rule_violations.",
        fact_keys=["modules", "modifiers", "mission_critical", "safety_critical", "tech_challenges", "obsolescence_candidates", "rule_violations", "rules_flags"],
        exemplar_pattern="risk",
    ),
    SectionDef(
        name="MOSA & Data Rights",
        schema_class=AcqMosaSection,
        instructions=(
            "Write a 1–2 paragraph mosa_approach stating the program's modular strategy and MIG reference. "
            "Then produce one module_sustainability entry per module: state the scenario_type (reprocure/reuse/recompete) "
            "drawn directly from scenarios data, list the interface_standards that govern that module's boundary, "
            "explain in competition_rationale how those standards enable the scenario (independent award, upgrade path, "
            "or technology refresh without re-engineering adjacent modules), and specify data_rights_required. "
            "If HW_SW_SEPARATION modifier active, treat hardware platform and software payload as separate modules "
            "with distinct boundaries even if not listed separately. "
            "Close with a data_rights_approach paragraph covering the program-wide strategy."
        ),
        fact_keys=["modules", "mig_id", "standards", "scenarios", "commercial_solutions", "obsolescence_candidates", "rule_violations", "rules_flags"],
        exemplar_pattern="mosa",
    ),
    SectionDef(
        name="Contracting Strategy",
        schema_class=AcqContractingSection,
        instructions="Describe contracting vehicle, competition strategy, and test/verification approach. If EMPHASIZE_COMMERCIAL modifier is active, prioritize commercial-first strategy.",
        fact_keys=["dev_cost_estimate", "attritable", "cots_count", "service_branch", "commercial_solutions", "modifiers", "rule_violations"],
        exemplar_pattern="contract",
    ),
]

_SEP_SECTIONS: list[SectionDef] = [
    SectionDef(
        name="Technical Reviews & Requirements",
        schema_class=SepTechSection,
        instructions="List technical review schedule (SRR, PDR, CDR, etc.) and describe requirements traceability approach.",
        fact_keys=["timeline_months", "mission_critical", "safety_critical", "program_description", "tech_challenges"],
        exemplar_pattern="technical review",
    ),
    SectionDef(
        name="Architecture & MOSA",
        schema_class=SepArchSection,
        instructions=(
            "Write a 1–2 paragraph architecture_description covering the system decomposition and MOSA approach. "
            "Then produce one module_boundaries entry per module: describe what crosses the boundary "
            "(data formats, control signals, RF interfaces, power), name the governing interface_standard, "
            "and state in enables what that standard boundary makes possible (independent recompete, "
            "technology insertion without adjacent re-design, government-directed upgrade). "
            "If HW_SW_SEPARATION modifier active, populate hw_sw_separation_note explaining how hardware "
            "and software are contractually and technically separated at this boundary. "
            "Close with mosa_compliance summarizing compliance posture against the applicable MIG."
        ),
        fact_keys=["modules", "standards", "mig_id", "scenarios", "software_standards", "rules_flags"],
        exemplar_pattern="architecture",
    ),
    SectionDef(
        name="Risk Management",
        schema_class=SepRiskSection,
        instructions="Generate 4–6 systems engineering risks with mitigations. Ground in tech_challenges, module flags, and rule_violations.",
        fact_keys=["modules", "modifiers", "safety_critical", "tech_challenges", "obsolescence_candidates", "rule_violations", "rules_flags"],
        exemplar_pattern="risk",
    ),
    SectionDef(
        name="Verification & Validation",
        schema_class=SepVnVSection,
        instructions="Describe V&V approach, including DO-178 if applicable. List test levels.",
        fact_keys=["modifiers", "safety_critical", "mission_critical", "software_large_part", "software_standards", "rules_flags"],
        exemplar_pattern="verification",
    ),
]

_MCP_SECTIONS: list[SectionDef] = [
    SectionDef(
        name="Conformance Overview",
        schema_class=McpOverviewSection,
        instructions="Write MOSA conformance plan overview and list 4–6 conformance objectives.",
        fact_keys=["program_name", "program_description", "mig_id", "modules", "scenarios"],
        exemplar_pattern="overview",
    ),
    SectionDef(
        name="Module Assessments",
        schema_class=McpModuleSection,
        instructions=(
            "Produce one module_assessments entry per module. "
            "Set scenario_type from scenarios data (reprocure/reuse/recompete); if no scenario is defined for a module, "
            "flag this as a gap in competition_enablement. "
            "In competition_enablement, state whether existing interface documentation (ICDs, SysML, API specs) "
            "is sufficient for a new vendor to compete without access to the incumbent's proprietary data. "
            "In interface_compliance, assess conformance to the applicable standards from the standards list. "
            "List module-specific risks (not program-wide risks). "
            "State a concrete verification_approach (analysis, inspection, demonstration, or test) "
            "rather than generic language."
        ),
        fact_keys=["modules", "standards", "scenarios", "rule_violations", "obsolescence_candidates"],
        exemplar_pattern="module",
    ),
    SectionDef(
        name="Verification Milestones",
        schema_class=McpVerificationSection,
        instructions="Define conformance verification milestones and assessment criteria.",
        fact_keys=["timeline_months", "mission_critical", "modules", "rule_violations"],
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
    scenario_rows: list,
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

    # Prefer MosaScenario table rows; fall back to wizard answer JSON blob
    if scenario_rows:
        scenarios = [
            {
                "scenario_type": s.scenario_type,
                "module_name": s.module_name,
                "description": s.description,
            }
            for s in scenario_rows
        ]
    else:
        scenarios_raw = wizard_answers.get("g_mosa_scenarios", "[]")
        try:
            scenarios = json.loads(scenarios_raw) if isinstance(scenarios_raw, str) else (scenarios_raw or [])
        except Exception:
            scenarios = []

    return {
        # Core identity
        "program_name": program.name,
        "service_branch": getattr(program, "service_branch", None),
        "army_pae": getattr(program, "army_pae", None),
        "mig_id": rules_result.mig_id,
        # Brief fields
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
        # Structured sub-objects
        "modules": module_list,
        "cots_count": sum(1 for m in module_list if m.get("cots_candidate")),
        "scenarios": scenarios,
        "standards": standard_list,
        # Named wizard answer fields (sliceable per section)
        "tech_challenges": wizard_answers.get("f_tech_challenges_and_risk_areas"),
        "similar_programs": wizard_answers.get("e_similar_previous_programs"),
        "obsolescence_candidates": wizard_answers.get("j_obsolescence_candidates"),
        "commercial_solutions": wizard_answers.get("k_commercial_solutions_by_module"),
        "software_standards": wizard_answers.get("n_software_standards_architectures"),
        # Rules engine outputs
        "modifiers": [m.value for m in rules_result.modifiers],
        "rule_violations": [
            {"rule_id": v.rule_id, "severity": v.severity, "message": v.message}
            for v in rules_result.violations
        ],
        "rules_flags": rules_result.flags,
        "recommended_module_count_min": rules_result.recommended_module_count_min,
        "recommended_module_count_max": rules_result.recommended_module_count_max,
    }


def _slice_fact_pack(full: dict, keys: list[str]) -> dict:
    """Return only the keys this section needs."""
    return {k: full[k] for k in keys if k in full}


def _load_program_data(db: Session, program_id: int) -> dict[str, Any]:
    """
    Load all program data needed for generation and return a prepared full_facts dict.
    Single source of truth used by both generate_document and generate_single_section.
    Raises ValueError if the program does not exist.
    """
    program = db.query(models.Program).filter_by(id=program_id).first()
    if not program:
        raise ValueError(f"Program {program_id} not found")

    brief = db.query(models.ProgramBrief).filter_by(program_id=program_id).first()
    modules = db.query(models.Module).filter_by(program_id=program_id).all()
    answers_rows = db.query(models.ProgramAnswer).filter_by(program_id=program_id).all()
    wizard_answers = {r.question_id: r.answer_text for r in answers_rows}

    try:
        from models_v2 import ProgramStandard
        standards = db.query(ProgramStandard).filter_by(program_id=program_id).all()
    except Exception:
        standards = []

    try:
        from models_v2 import MosaScenario
        scenario_rows = db.query(MosaScenario).filter_by(program_id=program_id).all()
    except Exception:
        scenario_rows = []

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

    full_facts = _build_full_fact_pack(
        program, brief, modules, wizard_answers, standards, rules_result, scenario_rows
    )
    # Attach the program ORM object so callers can read program.name etc.
    full_facts["_program"] = program
    full_facts["_rules_result"] = rules_result
    return full_facts


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def generate_document(
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

    full_facts = _load_program_data(db, program_id)
    program = full_facts.pop("_program")
    rules_result = full_facts.pop("_rules_result")

    # ---- Generate sections ----
    section_defs = SECTION_MAP[doc_type]
    assembled: dict[str, Any] = {}
    section_tracking: dict[str, Any] = {}

    for sec in section_defs:
        logger.info("Generating section '%s' for program %d (%s)", sec.name, program_id, doc_type)

        chunks = _retrieve_chunks_for_section(db, program_id, sec, full_facts)
        style_excerpt = _get_exemplar_style(db, program_id, doc_type, sec.exemplar_pattern)
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

        tracking = track_section(fact_pack, chunks, section_output)
        section_tracking[sec.name] = tracking.model_dump()

    assembled["_meta"] = {
        "program_id": program_id,
        "doc_type": doc_type,
        "mig_id": rules_result.mig_id,
        "modifiers": [m.value for m in rules_result.modifiers],
        "section_tracking": section_tracking,
    }

    return assembled


def generate_single_section(
    *,
    db: Session,
    program_id: int,
    doc_type: str,
    section_name: str,
) -> dict[str, Any]:
    """
    Regenerate one named section for program_id without touching the others.

    Returns {section_name: <section output dict>, "_tracking": {section_name: ...}}.
    Raises ValueError if doc_type or section_name is unknown.
    """
    if doc_type not in SECTION_MAP:
        raise ValueError(f"Unknown doc_type: {doc_type!r}")

    section_defs = SECTION_MAP[doc_type]
    sec = next((s for s in section_defs if s.name == section_name), None)
    if sec is None:
        known = [s.name for s in section_defs]
        raise ValueError(f"Unknown section {section_name!r} for {doc_type!r}. Known: {known}")

    full_facts = _load_program_data(db, program_id)
    program = full_facts.pop("_program")
    rules_result = full_facts.pop("_rules_result")

    chunks = _retrieve_chunks_for_section(db, program_id, sec, full_facts)
    style_excerpt = _get_exemplar_style(db, program_id, doc_type, sec.exemplar_pattern)
    fact_pack = _slice_fact_pack(full_facts, sec.fact_keys)

    logger.info("Regenerating section '%s' for program %d (%s)", sec.name, program_id, doc_type)
    output = generate_section(
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
    tracking = track_section(fact_pack, chunks, output)
    return {
        sec.name: output,
        "_tracking": {sec.name: tracking.model_dump()},
    }


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

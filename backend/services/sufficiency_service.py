"""
Sufficiency service — computes a GREEN/YELLOW/RED readiness score for a program.

No LLM calls. Pure data inspection + rules engine.
"""
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from rules import RulesInput, evaluate_rules


class SufficiencyLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW_HIGH = "YELLOW_HIGH"
    YELLOW_LOW = "YELLOW_LOW"
    RED = "RED"


# ---------------------------------------------------------------------------
# Gate definitions — any failure → RED
# ---------------------------------------------------------------------------

GATES = [
    ("PROGRAM_NAME",   "Program name must be set"),
    ("DESCRIPTION",    "Program description must be set"),
    ("SERVICE_BRANCH", "Service branch must be selected"),
    ("MODULES_EXIST",  "At least one module must be defined"),
]

# ---------------------------------------------------------------------------
# Coverage fields: (field_id, label, weight, source)
# Weights sum to 100.
# ---------------------------------------------------------------------------

COVERAGE_FIELDS = [
    ("program_description",   "Program Description",     15.0, "brief"),
    ("service_branch",        "Service Branch",           8.0, "program"),
    ("dev_cost_estimate",     "Dev Cost Estimate",        7.0, "brief"),
    ("production_unit_cost",  "Production Unit Cost",     5.0, "brief"),
    ("timeline_months",       "Timeline (months)",        6.0, "brief"),
    ("attritable",            "Attritable Flag",          4.0, "brief"),
    ("mission_critical",      "Mission Critical",         4.0, "brief"),
    ("safety_critical",       "Safety Critical",          4.0, "brief"),
    ("software_large_part",   "Software Dominant",        3.0, "brief"),
    ("modules_defined",       "Modules Defined",         20.0, "module"),
    ("scenarios_defined",     "MOSA Scenarios (≥2)",     12.0, "wizard"),
    ("standards_defined",     "Standards Identified",     7.0, "standard"),
    ("files_uploaded",        "Supporting Files",         5.0, "file"),
]


@dataclass
class GateResult:
    gate_id: str
    passed: bool
    message: str


@dataclass
class FieldCoverage:
    field_id: str
    label: str
    weight: float
    present: bool
    source: str


@dataclass
class SufficiencyResult:
    level: SufficiencyLevel
    score: float
    gates: List[GateResult]
    coverage: List[FieldCoverage]
    missing_critical: List[str]
    warnings: List[str]
    # Pass-through from rules engine
    mig_id: Optional[str] = None
    modifiers: list = field(default_factory=list)
    rule_violations: list = field(default_factory=list)


def compute_sufficiency(
    *,
    program: dict,
    brief: Optional[dict],
    modules: list,
    scenarios: list,          # list of MosaScenario ORM rows (canonical source)
    standards: list,
    file_count: int,
    wizard_answers: dict = (), # kept for backward compat; no longer used for scenarios
) -> SufficiencyResult:
    """
    Args:
        program:        dict from Program ORM (id, name, service_branch, army_pae, mig_id)
        brief:          dict from ProgramBrief ORM or None
        modules:        list of Module ORM rows
        scenarios:      list of MosaScenario ORM rows (canonical — NOT wizard_answers)
        standards:      list of ProgramStandard ORM rows
        file_count:     count of program_input files for this program
        wizard_answers: kept for signature compat; no longer used
    """
    brief = brief or {}

    # ---- Evaluate gates ----
    gate_checks = {
        "PROGRAM_NAME":   bool(program.get("name")),
        "DESCRIPTION":    bool(brief.get("program_description")),
        "SERVICE_BRANCH": bool(program.get("service_branch")),
        "MODULES_EXIST":  len(modules) > 0,
    }
    gates = [GateResult(g, gate_checks[g], msg) for g, msg in GATES]
    gates_failed = [g for g in gates if not g.passed]

    # ---- Evaluate coverage ----
    present_map: dict[str, bool] = {
        "program_description":  bool(brief.get("program_description")),
        "service_branch":       bool(program.get("service_branch")),
        "dev_cost_estimate":    brief.get("dev_cost_estimate") is not None,
        "production_unit_cost": brief.get("production_unit_cost") is not None,
        "timeline_months":      brief.get("timeline_months") is not None,
        "attritable":           brief.get("attritable") is not None,
        "mission_critical":     brief.get("mission_critical") is not None,
        "safety_critical":      brief.get("safety_critical") is not None,
        "software_large_part":  brief.get("software_large_part") is not None,
        "modules_defined":      len(modules) > 0,
        "scenarios_defined":    len([s for s in scenarios if getattr(s, 'description', '') or '']) >= 2,
        "standards_defined":    len(standards) >= 1,
        "files_uploaded":       file_count >= 1,
    }

    coverage: List[FieldCoverage] = []
    earned = 0.0
    for fid, label, weight, source in COVERAGE_FIELDS:
        present = present_map.get(fid, False)
        if present:
            earned += weight
        coverage.append(FieldCoverage(fid, label, weight, present, source))

    score = round(earned, 1)
    missing_critical = [c.label for c in coverage if not c.present and c.weight >= 8.0]
    warnings = [c.label for c in coverage if not c.present and 4.0 <= c.weight < 8.0]

    # ---- Determine level ----
    if gates_failed:
        level = SufficiencyLevel.RED
    elif score >= 80:
        level = SufficiencyLevel.GREEN
    elif score >= 55:
        level = SufficiencyLevel.YELLOW_HIGH
    else:
        level = SufficiencyLevel.YELLOW_LOW

    # ---- Run rules engine ----
    module_list = modules or []
    rules_inp = RulesInput(
        service_branch=program.get("service_branch"),
        army_pae=program.get("army_pae"),
        dev_cost_estimate=brief.get("dev_cost_estimate"),
        production_unit_cost=brief.get("production_unit_cost"),
        attritable=brief.get("attritable"),
        sustainment_tail=brief.get("sustainment_tail"),
        software_large_part=brief.get("software_large_part"),
        software_involved=brief.get("software_involved"),
        mission_critical=brief.get("mission_critical"),
        safety_critical=brief.get("safety_critical"),
        similar_programs_exist=brief.get("similar_programs_exist"),
        timeline_months=brief.get("timeline_months"),
        module_count=len(module_list),
        modules_with_cots=sum(1 for m in module_list if getattr(m, "cots_candidate", False)),
        modules_with_tech_risk=sum(1 for m in module_list if getattr(m, "tech_risk", False)),
        modules_with_obsolescence_risk=sum(1 for m in module_list if getattr(m, "obsolescence_risk", False)),
    )
    rules = evaluate_rules(rules_inp)

    return SufficiencyResult(
        level=level,
        score=score,
        gates=gates,
        coverage=coverage,
        missing_critical=missing_critical,
        warnings=warnings,
        mig_id=rules.mig_id,
        modifiers=[m.value for m in rules.modifiers],
        rule_violations=[
            {"rule_id": v.rule_id, "severity": v.severity, "message": v.message}
            for v in rules.violations
        ],
    )

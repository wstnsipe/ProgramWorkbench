"""
Deterministic MOSA rules engine — no LLM calls.

All rules are pure Python. Given a RulesInput snapshot of program data,
returns a RulesResult with:
  - mig_id: auto-selected Modular Implementation Guide
  - modifiers: DocModifier flags injected into LLM system prompts
  - violations: ERROR/WARN/INFO findings
  - recommended module count range
"""
from .models import DocModifier, RulesInput, RulesResult, RuleViolation

# ---------------------------------------------------------------------------
# MIG lookup tables
# ---------------------------------------------------------------------------

_SERVICE_TO_MIG: dict[str, str] = {
    "USN": "MIG-USN-2022",
    "USAF": "MIG-USAF-2021",
    "USSF": "MIG-USSF-2023",
    "ARMY": "MIG-ARMY-2022",
}

_ARMY_PAE_TO_MIG: dict[str, str] = {
    "PM_PEO_C3T": "MIG-ARMY-C3T-2022",
    "PM_PEO_IEW_S": "MIG-ARMY-IEWS-2022",
}

# ---------------------------------------------------------------------------
# Module count bands by development cost ($M)
# ---------------------------------------------------------------------------

_COST_MODULE_BANDS: list[tuple[float, int, int]] = [
    (50.0,   3,  5),   # < $50M
    (200.0,  5,  8),   # $50M – $200M
    (500.0,  7, 12),   # $200M – $500M
    (float("inf"), 10, 20),  # > $500M
]


def _module_count_for_cost(cost_m: float) -> tuple[int, int]:
    for threshold, lo, hi in _COST_MODULE_BANDS:
        if cost_m < threshold:
            return lo, hi
    return 10, 20  # fallback


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def evaluate_rules(inp: RulesInput) -> RulesResult:
    result = RulesResult()
    violations: list[RuleViolation] = []

    # Rule 1 — MIG auto-selection
    if inp.service_branch:
        if inp.service_branch == "ARMY" and inp.army_pae and inp.army_pae in _ARMY_PAE_TO_MIG:
            result.mig_id = _ARMY_PAE_TO_MIG[inp.army_pae]
        else:
            result.mig_id = _SERVICE_TO_MIG.get(inp.service_branch)

    # Rule 2 — Cost-based module count recommendation
    if inp.dev_cost_estimate is not None:
        lo, hi = _module_count_for_cost(inp.dev_cost_estimate)
        result.recommended_module_count_min = lo
        result.recommended_module_count_max = hi

        if inp.module_count > 0:
            if inp.module_count < lo:
                violations.append(RuleViolation(
                    rule_id="MODULE_COUNT_LOW",
                    severity="WARN",
                    message=(
                        f"Program cost of ${inp.dev_cost_estimate:.0f}M suggests {lo}–{hi} modules; "
                        f"only {inp.module_count} defined."
                    ),
                    field="module_count",
                ))
            elif inp.module_count > hi:
                violations.append(RuleViolation(
                    rule_id="MODULE_COUNT_HIGH",
                    severity="INFO",
                    message=(
                        f"Program has {inp.module_count} modules, above recommended maximum of {hi} "
                        f"for a ${inp.dev_cost_estimate:.0f}M program. Verify boundary definitions."
                    ),
                    field="module_count",
                ))

    # Rule 3 — Software-heavy or safety-critical → DO-178 / DO-297
    if inp.software_large_part or inp.safety_critical:
        result.modifiers.append(DocModifier.INCLUDE_DO178_DO297)
        result.modifiers.append(DocModifier.HW_SW_SEPARATION)
        result.flags["do178_applicable"] = True

    # Rule 4 — Mission critical → verification emphasis
    if inp.mission_critical:
        result.modifiers.append(DocModifier.MISSION_CRITICAL_VERIFICATION)

    # Rule 5 — Attritable → planned obsolescence language
    if inp.attritable:
        result.modifiers.append(DocModifier.ATTRITABLE_LIFECYCLE)
        violations.append(RuleViolation(
            rule_id="ATTRITABLE_SUSTAINMENT",
            severity="INFO",
            message="Attritable programs require explicit planned-obsolescence language in Acq Strategy.",
        ))

    # Rule 6 — Long sustainment tail → sustainment planning section emphasis
    if inp.sustainment_tail:
        result.modifiers.append(DocModifier.SUSTAINMENT_TAIL_PLANNING)

    # Rule 7 — High proportion of tech-risk modules → modular approach emphasis
    tech_risk_ratio = inp.modules_with_tech_risk / max(inp.module_count, 1) if inp.module_count else 0
    if tech_risk_ratio >= 0.4:
        result.modifiers.append(DocModifier.HIGH_TECH_RISK_MODULAR)
        result.flags["high_tech_risk"] = True

    # Rule 8 — COTS candidates → commercial-first language
    if inp.modules_with_cots > 0:
        result.modifiers.append(DocModifier.EMPHASIZE_COMMERCIAL)
        result.modifiers.append(DocModifier.COTS_REFRESH_CYCLE)

    # Rule 9 — Similar programs exist but no modules → reuse type required
    if inp.similar_programs_exist and inp.module_count == 0:
        result.modifiers.append(DocModifier.REUSE_TYPE_ANALYSIS)
        violations.append(RuleViolation(
            rule_id="REUSE_TYPE_MISSING",
            severity="WARN",
            message="Similar programs exist — reuse type analysis (adapt / adopt / extend) required in modules.",
        ))

    # Rule 10 — Short timeline → compression justification
    if inp.timeline_months is not None and inp.timeline_months < 18:
        violations.append(RuleViolation(
            rule_id="TIMELINE_SHORT",
            severity="WARN",
            message=f"Timeline of {inp.timeline_months} months is below 18-month threshold; include schedule compression rationale.",
            field="timeline_months",
        ))

    # Rule 11 — No modules but generation requested (hard gate upstream, logged here)
    if inp.module_count == 0:
        violations.append(RuleViolation(
            rule_id="NO_MODULES",
            severity="WARN",
            message="No modules defined. MOSA analysis sections will be placeholder-only.",
        ))

    # Rule 12 — Obsolescence risk flag
    obs_ratio = inp.modules_with_obsolescence_risk / max(inp.module_count, 1) if inp.module_count else 0
    if obs_ratio >= 0.3:
        result.flags["high_obsolescence_risk"] = True
        violations.append(RuleViolation(
            rule_id="OBSOLESCENCE_HIGH",
            severity="INFO",
            message=f"{inp.modules_with_obsolescence_risk} of {inp.module_count} modules flagged for obsolescence risk; recommend DMSMS planning section.",
        ))

    # Deduplicate modifiers while preserving order
    seen: set = set()
    deduped = []
    for m in result.modifiers:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    result.modifiers = deduped
    result.violations = violations

    return result

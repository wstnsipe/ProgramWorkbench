"""
Module-to-scenario mismatch rules — no LLM, no DB access.

Checks:
  SCENARIO_MODULE_UNREF  — a module name is not referenced in any scenario
  SCENARIO_MODULE_UNKNOWN — a scenario references a module_name not in the module list
"""
from typing import List

from .models import RuleViolation


def check_mismatches(
    module_names: List[str],
    scenario_module_names: List[str],   # scenario.module_name fields (may be empty string)
    scenario_descriptions: List[str],   # scenario.description fields
) -> List[RuleViolation]:
    violations: List[RuleViolation] = []

    if not module_names:
        return violations

    lower_module_names = [n.lower() for n in module_names]

    # Build a flat text blob of all scenario content for substring search
    all_scenario_text = " ".join(
        (s or "").lower() for s in scenario_module_names + scenario_descriptions
    )

    # Rule A — module not referenced anywhere in scenarios
    for name in module_names:
        if name.lower() not in all_scenario_text:
            violations.append(RuleViolation(
                rule_id="SCENARIO_MODULE_UNREF",
                severity="WARN",
                message=f'Module "{name}" is not referenced in any MOSA scenario.',
                field="scenarios",
            ))

    # Rule B — scenario's explicit module_name doesn't match any known module
    seen_unknown: set = set()
    for ref in scenario_module_names:
        ref = (ref or "").strip()
        if not ref:
            continue
        if ref.lower() not in lower_module_names and ref.lower() not in seen_unknown:
            seen_unknown.add(ref.lower())
            violations.append(RuleViolation(
                rule_id="SCENARIO_MODULE_UNKNOWN",
                severity="WARN",
                message=f'Scenario references "{ref}" which does not match any defined module.',
                field="scenarios",
            ))

    return violations

"""
Module-to-scenario mismatch rules — no LLM, no DB access.

Checks:
  SCENARIO_MODULE_UNREF     — a module name is not referenced in any scenario
  SCENARIO_MODULE_UNKNOWN   — a scenario description names a module not in the module list
  MODULE_DESC_NO_COVERAGE   — a module has a description but no scenario mentions it
"""
import re
from typing import List, Optional

from .models import RuleViolation

# Matches "For the <name> module, the USG desires the ability to"
_FORMAT_RE = re.compile(r'For the (.+?) module', re.IGNORECASE)


def _extract_module_name_from_description(description: str) -> Optional[str]:
    """Return the module name embedded in the standard MOSA format, or None."""
    m = _FORMAT_RE.search(description or "")
    return m.group(1).strip() if m else None


def check_mismatches(
    module_names: List[str],
    scenario_module_names: List[str],   # scenario.module_name fields (may be empty)
    scenario_descriptions: List[str],   # scenario.description fields
    module_descriptions: Optional[List[str]] = None,  # module.description fields
) -> List[RuleViolation]:
    violations: List[RuleViolation] = []

    if not module_names:
        return violations

    lower_module_names = [n.lower() for n in module_names]
    filled_descriptions = [d for d in scenario_descriptions if (d or "").strip()]

    # Build a flat text blob of all scenario content for substring search
    all_scenario_text = " ".join(
        (s or "").lower() for s in scenario_module_names + scenario_descriptions
    )

    # Rule A — module name not referenced anywhere in scenario text
    for name in module_names:
        if name.lower() not in all_scenario_text:
            violations.append(RuleViolation(
                rule_id="SCENARIO_MODULE_UNREF",
                severity="WARN",
                message=f'Module "{name}" is not referenced in any MOSA scenario.',
                field="scenarios",
            ))

    # Rule B — module name extracted from description format doesn't match any known module
    # Covers both explicit module_name field and the "For the X module..." prefix in descriptions.
    seen_unknown: set = set()
    candidates = list(scenario_module_names)
    for desc in scenario_descriptions:
        extracted = _extract_module_name_from_description(desc or "")
        if extracted:
            candidates.append(extracted)

    for ref in candidates:
        ref = (ref or "").strip()
        if not ref:
            continue
        ref_lower = ref.lower()
        if ref_lower in seen_unknown:
            continue
        # Accept if ref is a substring of a known module name or vice versa
        matched = any(
            ref_lower in k or k in ref_lower for k in lower_module_names
        )
        if not matched:
            seen_unknown.add(ref_lower)
            violations.append(RuleViolation(
                rule_id="SCENARIO_MODULE_UNKNOWN",
                severity="WARN",
                message=f'Scenario references "{ref}" which does not match any defined module.',
                field="scenarios",
            ))

    # Rule C — module has a description but no scenario mentions it
    # Only fires when module descriptions are provided and module isn't covered by Rule A.
    if module_descriptions:
        for name, desc in zip(module_names, module_descriptions):
            has_desc = bool((desc or "").strip())
            already_warned = any(
                v.rule_id == "SCENARIO_MODULE_UNREF" and f'"{name}"' in v.message
                for v in violations
            )
            if has_desc and already_warned and filled_descriptions:
                # Upgrade the message to note the description exists
                for v in violations:
                    if v.rule_id == "SCENARIO_MODULE_UNREF" and f'"{name}"' in v.message:
                        v.message = (
                            f'Module "{name}" has a description but no MOSA scenario — '
                            f'add a scenario using the required format.'
                        )
                        v.rule_id = "MODULE_DESC_NO_COVERAGE"

    return violations

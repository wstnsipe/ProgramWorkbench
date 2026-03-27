"""
generation/tracking.py — Post-generation assumptions and evidence tracking.

Assumptions are parsed deterministically from [ASSUMPTION: ...] markers in
the generated text; no LLM call required.

Evidence is built from which fact_pack keys were non-null (structured inputs)
and how many RAG chunks were retrieved (file evidence). Both are known before
the LLM call and captured without asking the model to self-report.
"""
import re
from typing import Any
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class Assumption(BaseModel):
    field: str      # output field containing the assumption, e.g. "development" or "risks.0.mitigation"
    text: str       # assumption text extracted from [ASSUMPTION: ...]


class Evidence(BaseModel):
    source_type: str    # "structured_input" | "wizard_answer" | "file_chunk"
    key: str            # fact_pack key or "chunks:N"
    label: str          # human-readable description


class SectionTracking(BaseModel):
    assumptions: list[Assumption] = []
    evidence: list[Evidence] = []

    @property
    def has_assumptions(self) -> bool:
        return len(self.assumptions) > 0


# ---------------------------------------------------------------------------
# Human-readable labels for fact_pack keys
# ---------------------------------------------------------------------------

_KEY_LABELS: dict[str, str] = {
    "program_name":                  "Program name",
    "service_branch":                "Service branch",
    "army_pae":                      "Army PAE",
    "mig_id":                        "MIG ID",
    "program_description":           "Program description",
    "dev_cost_estimate":             "Development cost estimate ($M)",
    "production_unit_cost":          "Production unit cost ($M)",
    "timeline_months":               "Program timeline (months)",
    "attritable":                    "Attritable flag",
    "sustainment_tail":              "Sustainment tail flag",
    "software_large_part":           "Software-dominant flag",
    "mission_critical":              "Mission critical flag",
    "safety_critical":               "Safety critical flag",
    "similar_programs_exist":        "Similar programs flag",
    "modules":                       "Module definitions",
    "scenarios":                     "MOSA scenarios",
    "standards":                     "Standards list",
    "tech_challenges":               "Tech challenges (wizard)",
    "similar_programs":              "Similar programs (wizard)",
    "obsolescence_candidates":       "Obsolescence candidates (wizard)",
    "commercial_solutions":          "Commercial solutions (wizard)",
    "software_standards":            "Software standards (wizard)",
    "rules_flags":                   "Rules engine flags",
    "recommended_module_count_min":  "Recommended module range (min)",
    "recommended_module_count_max":  "Recommended module range (max)",
    "cots_count":                    "COTS module count",
}

_WIZARD_KEYS: frozenset[str] = frozenset({
    "tech_challenges", "similar_programs", "obsolescence_candidates",
    "commercial_solutions", "software_standards",
})

# Keys that are already surfaced in the system prompt; not listed separately as evidence
_PROMPT_KEYS: frozenset[str] = frozenset({"rule_violations", "modifiers"})

_ASSUMPTION_RE = re.compile(r'\[ASSUMPTION:\s*([^\]]+)\]', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_from_value(field_path: str, value: Any, out: list[Assumption]) -> None:
    """Recursively scan a value for [ASSUMPTION: ...] markers."""
    if isinstance(value, str):
        for m in _ASSUMPTION_RE.finditer(value):
            out.append(Assumption(field=field_path, text=m.group(1).strip()))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _extract_from_value(f"{field_path}[{i}]", item, out)
    elif isinstance(value, dict):
        for k, v in value.items():
            _extract_from_value(f"{field_path}.{k}", v, out)


def extract_assumptions(content: dict[str, Any]) -> list[Assumption]:
    """
    Parse all [ASSUMPTION: ...] markers from a generated section output dict.
    Returns a flat list of Assumption objects.
    """
    found: list[Assumption] = []
    for field, value in content.items():
        _extract_from_value(field, value, found)
    return found


def build_evidence(fact_pack: dict[str, Any], retrieved_chunks: list[str]) -> list[Evidence]:
    """
    Build an evidence list from non-null fact_pack keys and chunk count.
    Only keys that actually contained data are included.
    """
    evidence: list[Evidence] = []

    for key, value in fact_pack.items():
        if key in _PROMPT_KEYS:
            continue
        # Skip empty / null values — they contributed nothing
        if value is None or value == [] or value == {}:
            continue
        source_type = "wizard_answer" if key in _WIZARD_KEYS else "structured_input"
        label = _KEY_LABELS.get(key, key.replace("_", " ").title())
        evidence.append(Evidence(source_type=source_type, key=key, label=label))

    if retrieved_chunks:
        evidence.append(Evidence(
            source_type="file_chunk",
            key=f"chunks:{len(retrieved_chunks)}",
            label=f"{len(retrieved_chunks)} uploaded file excerpt(s)",
        ))

    return evidence


def track_section(
    fact_pack: dict[str, Any],
    retrieved_chunks: list[str],
    content: dict[str, Any],
) -> SectionTracking:
    """
    Build a SectionTracking record for one completed section.
    Call after generate_section() returns validated content.
    """
    return SectionTracking(
        assumptions=extract_assumptions(content),
        evidence=build_evidence(fact_pack, retrieved_chunks),
    )

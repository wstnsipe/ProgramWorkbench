"""
Canonical document templates for the ACQ Program Workbench.

Each entry in TEMPLATE_REGISTRY defines:
  section_order     – Exact heading strings in render order.  These are the
                      immutable "contract" between the template and the docx
                      builders; heading text must not drift between the two.
  required_sections – Subset of section_order that must always be present.
                      Optional/appendix sections are omitted from this list.
  section_format    – Per-section format hint consumed by smart generators:
                        "narrative" – flowing prose paragraphs
                        "bullet"    – bulleted / numbered list items
                        "mixed"     – narrative intro followed by bullets or a table
                        "table"     – structured tabular data
  required_fields   – Wizard answer keys (from the `answers` dict) that must
                      be non-empty for a meaningful document to be produced.
                      Generators may warn or refuse if these are absent.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Type alias (kept lightweight; no runtime dependency on typing_extensions)
# ---------------------------------------------------------------------------

SectionFormat = str  # "narrative" | "bullet" | "mixed" | "table"

TemplateSpec = dict  # {section_order, required_sections, section_format, required_fields}

TEMPLATE_REGISTRY: dict[str, TemplateSpec] = {
    # ------------------------------------------------------------------
    # Request for Information
    # Canonical source: build_smart_rfi() in docx_builder.py
    # ------------------------------------------------------------------
    "rfi": {
        "display_name": "Request for Information (RFI)",
        "section_order": [
            "1. Document Overview",
            "2. RFI Purpose",
            "3. Program Context",
            "4. MOSA Requirements",
            "5. Candidate Module Summary",
            "6. Questions to Industry",
            "7. Requested Deliverables",
            "8. Submission Instructions",
            "Appendix A: Sources Used",
        ],
        "required_sections": [
            "1. Document Overview",
            "2. RFI Purpose",
            "3. Program Context",
            "4. MOSA Requirements",
            "5. Candidate Module Summary",
            "6. Questions to Industry",
            "7. Requested Deliverables",
            "8. Submission Instructions",
        ],
        "section_format": {
            "1. Document Overview": "narrative",
            "2. RFI Purpose": "narrative",
            "3. Program Context": "narrative",
            "4. MOSA Requirements": "bullet",
            "5. Candidate Module Summary": "table",
            "6. Questions to Industry": "bullet",
            "7. Requested Deliverables": "bullet",
            "8. Submission Instructions": "narrative",
            "Appendix A: Sources Used": "bullet",
        },
        "required_fields": [
            "a_program_description",
            "g_mosa_scenarios",
        ],
    },

    # ------------------------------------------------------------------
    # Systems Engineering Plan
    # Canonical source: build_sep_smart() in docx_builder.py
    # Per OSD SEP Guide v4.1 / DoDI 5000.02
    # ------------------------------------------------------------------
    "sep": {
        "display_name": "Systems Engineering Plan (SEP)",
        "section_order": [
            "1. Executive Summary",
            "2. Program Overview",
            "3. Systems Engineering Strategy",
            "4. Technical Reviews",
            "5. Requirements Traceability",
            "6. System Architecture and MOSA",
            "7. Technical Risk Register",
            "8. Configuration Management",
            "9. Verification and Validation",
            "10. Data Management",
            "11. Specialty Engineering",
            "Appendix A: Glossary",
            "Appendix B: References",
            "Appendix C: Sources Used",
        ],
        "required_sections": [
            "1. Executive Summary",
            "2. Program Overview",
            "3. Systems Engineering Strategy",
            "4. Technical Reviews",
            "5. Requirements Traceability",
            "6. System Architecture and MOSA",
            "7. Technical Risk Register",
            "8. Configuration Management",
            "9. Verification and Validation",
            "10. Data Management",
            "11. Specialty Engineering",
        ],
        "section_format": {
            "1. Executive Summary": "narrative",
            "2. Program Overview": "narrative",
            "3. Systems Engineering Strategy": "mixed",
            "4. Technical Reviews": "mixed",
            "5. Requirements Traceability": "mixed",
            "6. System Architecture and MOSA": "mixed",
            "7. Technical Risk Register": "table",
            "8. Configuration Management": "narrative",
            "9. Verification and Validation": "mixed",
            "10. Data Management": "narrative",
            "11. Specialty Engineering": "mixed",
            "Appendix A: Glossary": "bullet",
            "Appendix B: References": "bullet",
            "Appendix C: Sources Used": "bullet",
        },
        "required_fields": [
            "a_program_description",
            "f_tech_challenges_and_risk_areas",
            "g_mosa_scenarios",
            "h_candidate_modules",
        ],
    },

    # ------------------------------------------------------------------
    # Acquisition Strategy
    # Canonical source: build_acq_strategy_smart() in docx_builder.py
    # ------------------------------------------------------------------
    "acq_strategy": {
        "display_name": "Acquisition Strategy",
        "section_order": [
            "1. Executive Summary",
            "2. Acquisition Approach",
            "3. Schedule and Milestones",
            "4. Cost Estimates",
            "5. Candidate Module Summary",
            "6. Modular Open Systems Approach (MOSA)",
            "7. Technical Data and Data Rights Strategy",
            "8. Standards and Constraints",
            "9. Test and Verification Strategy",
            "10. Contracting Strategy",
            "11. Risk Register",
            "Appendix A: Sources Used",
        ],
        "required_sections": [
            "1. Executive Summary",
            "2. Acquisition Approach",
            "3. Schedule and Milestones",
            "5. Candidate Module Summary",
            "6. Modular Open Systems Approach (MOSA)",
            "7. Technical Data and Data Rights Strategy",
            "10. Contracting Strategy",
            "11. Risk Register",
        ],
        "section_format": {
            "1. Executive Summary": "narrative",
            "2. Acquisition Approach": "narrative",
            "3. Schedule and Milestones": "mixed",
            "4. Cost Estimates": "mixed",
            "5. Candidate Module Summary": "table",
            "6. Modular Open Systems Approach (MOSA)": "mixed",
            "7. Technical Data and Data Rights Strategy": "narrative",
            "8. Standards and Constraints": "bullet",
            "9. Test and Verification Strategy": "narrative",
            "10. Contracting Strategy": "narrative",
            "11. Risk Register": "table",
            "Appendix A: Sources Used": "bullet",
        },
        "required_fields": [
            "a_program_description",
            "f_tech_challenges_and_risk_areas",
            "g_mosa_scenarios",
            "h_candidate_modules",
            "i_known_standards_architectures_mapping",
        ],
    },

    # ------------------------------------------------------------------
    # MOSA Conformance Plan
    # Canonical source: build_smart_mosa_conformance_plan() in docx_builder.py
    # Per 10 U.S.C. § 4401 / PEO AVN MOSA guidance
    # ------------------------------------------------------------------
    "mcp": {
        "display_name": "MOSA Conformance Plan (MCP)",
        "section_order": [
            "1. Executive Summary",
            "2. MOSA Objectives",
            "3. Tailoring Rationale",
            "4. Program Context",
            "5. Module Inventory and Conformance Status",
            "6. Interface Registry",
            "7. Standards and Architecture Mapping",
            "8. Technical Data and Data Rights",
            "9. Conformance Verification Plan",
            "10. MOSA Risk Register",
            "11. MOSA Self-Assessment Matrix",
            "12. MOSA Scenario Mapping",
            "Appendix A: Sources Used",
        ],
        "required_sections": [
            "1. Executive Summary",
            "2. MOSA Objectives",
            "3. Tailoring Rationale",
            "4. Program Context",
            "5. Module Inventory and Conformance Status",
            "6. Interface Registry",
            "7. Standards and Architecture Mapping",
            "9. Conformance Verification Plan",
            "10. MOSA Risk Register",
            "11. MOSA Self-Assessment Matrix",
        ],
        "section_format": {
            "1. Executive Summary": "narrative",
            "2. MOSA Objectives": "bullet",
            "3. Tailoring Rationale": "narrative",
            "4. Program Context": "narrative",
            "5. Module Inventory and Conformance Status": "table",
            "6. Interface Registry": "table",
            "7. Standards and Architecture Mapping": "mixed",
            "8. Technical Data and Data Rights": "narrative",
            "9. Conformance Verification Plan": "mixed",
            "10. MOSA Risk Register": "table",
            "11. MOSA Self-Assessment Matrix": "table",
            "12. MOSA Scenario Mapping": "mixed",
            "Appendix A: Sources Used": "bullet",
        },
        "required_fields": [
            "a_program_description",
            "g_mosa_scenarios",
            "i_known_standards_architectures_mapping",
            "h_candidate_modules",
        ],
    },
}


def get_template(doc_type: str) -> TemplateSpec:
    """Return the template spec for *doc_type*, raising KeyError if unknown."""
    if doc_type not in TEMPLATE_REGISTRY:
        known = ", ".join(TEMPLATE_REGISTRY)
        raise KeyError(f"Unknown doc_type {doc_type!r}. Known types: {known}")
    return TEMPLATE_REGISTRY[doc_type]


def section_format(doc_type: str, heading: str) -> SectionFormat:
    """Return the format hint for a specific section heading."""
    template = get_template(doc_type)
    return template["section_format"].get(heading, "narrative")


def is_required_section(doc_type: str, heading: str) -> bool:
    """Return True if *heading* is a required section for *doc_type*."""
    return heading in get_template(doc_type)["required_sections"]


# ---------------------------------------------------------------------------
# Section → Pydantic field mapping
#
# Maps each template section heading to the JSON key(s) that the LLM must
# use in its output.  These keys are the Pydantic field names on the plan
# schema (RfiPlan, AcqStrategyPlan, MosaPlan, SepPlan).
# ---------------------------------------------------------------------------

SECTION_FIELD_MAP: dict[str, dict[str, list[str]]] = {
    "rfi": {
        "1. Document Overview":          ["overview"],
        "2. RFI Purpose":                ["rfi_purpose"],
        "3. Program Context":            ["program_context"],
        "4. MOSA Requirements":          ["mosa_requirements"],
        "5. Candidate Module Summary":   ["module_table_rows"],
        "6. Questions to Industry":      ["questions_to_industry"],
        "7. Requested Deliverables":     ["requested_deliverables"],
        "8. Submission Instructions":    ["submission_instructions"],
        "Appendix A: Sources Used":      ["sources_used"],
    },
    "sep": {
        "1. Executive Summary":              ["executive_summary"],
        "2. Program Overview":               ["program_overview"],
        "3. Systems Engineering Strategy":   ["se_strategy"],
        "4. Technical Reviews":              ["tech_reviews"],
        "5. Requirements Traceability":      ["requirements_traceability"],
        "6. System Architecture and MOSA":   ["architecture_mosa"],
        "7. Technical Risk Register":        ["risk_register"],
        "8. Configuration Management":       ["config_mgmt"],
        "9. Verification and Validation":    ["vnv"],
        "10. Data Management":               ["data_mgmt"],
        "11. Specialty Engineering":         ["specialty_eng"],
        # Both appendix headings share the same "appendices" field object.
        "Appendix A: Glossary":              ["appendices"],
        "Appendix B: References":            [],   # sub-field of appendices
        "Appendix C: Sources Used":          ["sources_used"],
    },
    "acq_strategy": {
        "1. Executive Summary":                          ["executive_summary"],
        "2. Acquisition Approach":                       ["acquisition_approach"],
        "3. Schedule and Milestones":                    ["schedule_milestones"],
        "4. Cost Estimates":                             ["cost_estimates"],
        "5. Candidate Module Summary":                   ["module_table_rows"],
        "6. Modular Open Systems Approach (MOSA)":       ["mosa_approach", "mosa_bullets"],
        "7. Technical Data and Data Rights Strategy":    ["data_rights_approach"],
        "8. Standards and Constraints":                  ["standards_references"],
        "9. Test and Verification Strategy":             ["test_verification_approach"],
        "10. Contracting Strategy":                      ["contracting_strategy"],
        "11. Risk Register":                             ["risk_register"],
        "Appendix A: Sources Used":                      ["sources_used"],
    },
    "mcp": {
        "1. Executive Summary":                       ["executive_summary"],
        "2. MOSA Objectives":                         ["mosa_objectives"],
        "3. Tailoring Rationale":                     ["tailoring_rationale"],
        "4. Program Context":                         ["program_context"],
        "5. Module Inventory and Conformance Status": ["module_inventory"],
        "6. Interface Registry":                      ["interface_registry"],
        "7. Standards and Architecture Mapping":      ["standards_mapping"],
        "8. Technical Data and Data Rights":          ["data_rights_posture"],
        "9. Conformance Verification Plan":           ["verification_milestones"],
        "10. MOSA Risk Register":                     ["risk_register"],
        "11. MOSA Self-Assessment Matrix":            ["assessment_matrix"],
        "12. MOSA Scenario Mapping":                  ["mosa_scenarios"],
        "Appendix A: Sources Used":                   ["sources_used"],
    },
}

# Fields that appear in the JSON output but are not tied to a specific section
# heading (metadata / citations).  Always allowed for every doc type.
_ALWAYS_ALLOWED: frozenset[str] = frozenset({"citations", "title_block"})

# Plain-string Pydantic fields per doc type.  Only these receive a
# "Not provided" default when a required section is unpopulatable.
# List, table, and structured-object fields default to [] / their zero value.
_STRING_FIELDS: dict[str, frozenset[str]] = {
    "rfi": frozenset({"overview", "rfi_purpose", "program_context"}),
    "sep": frozenset({"executive_summary", "program_overview", "se_strategy"}),
    "acq_strategy": frozenset({
        "executive_summary", "acquisition_approach", "mosa_approach",
        "data_rights_approach", "test_verification_approach", "contracting_strategy",
    }),
    "mcp": frozenset({
        "executive_summary", "tailoring_rationale", "program_context", "data_rights_posture",
    }),
}


def allowed_fields(doc_type: str) -> frozenset[str]:
    """Return all JSON field names the LLM may emit for *doc_type*."""
    mapping = SECTION_FIELD_MAP.get(doc_type, {})
    fields: set[str] = set(_ALWAYS_ALLOWED)
    for section_fields in mapping.values():
        fields.update(section_fields)
    return frozenset(fields)


def normalize_llm_output(doc_type: str, raw_data: dict) -> dict:
    """Validate and normalize the raw LLM JSON dict against the template.

    Steps
    -----
    1. Collect any JSON keys not present in the allowed field set for this
       doc_type and raise ``ValueError`` listing them.  Callers should
       convert this to HTTP 400.
    2. For each required section's *string* fields: if the value is absent
       or blank, replace it with the sentinel ``"Not provided"`` so the
       docx builder always receives a non-empty string.

    Returns the (possibly mutated) *raw_data* dict.
    """
    allowed = allowed_fields(doc_type)
    unknown = sorted(k for k in raw_data if k not in allowed)
    if unknown:
        raise ValueError(
            f"LLM output contains fields not in the '{doc_type}' template: "
            + ", ".join(unknown)
        )

    tmpl = TEMPLATE_REGISTRY[doc_type]
    required_sections = set(tmpl["required_sections"])
    str_fields = _STRING_FIELDS.get(doc_type, frozenset())
    mapping = SECTION_FIELD_MAP.get(doc_type, {})

    for section, fields in mapping.items():
        if section not in required_sections:
            continue
        for field in fields:
            if field not in str_fields:
                continue
            val = raw_data.get(field)
            if not val or (isinstance(val, str) and not val.strip()):
                raw_data[field] = "Not provided"

    return raw_data


def build_template_contract(doc_type: str) -> str:
    """Return a system-prompt block that enforces template conformance.

    Instructs the LLM on:
    - The exact JSON keys it may use (derived from SECTION_FIELD_MAP).
    - Which sections are required vs optional.
    - The sentinel rule ("Not provided") for unpopulatable required strings.
    - The prohibition on extra keys.
    """
    tmpl = TEMPLATE_REGISTRY.get(doc_type, {})
    section_order: list[str] = tmpl.get("section_order", [])
    required_sections: set[str] = set(tmpl.get("required_sections", []))
    mapping = SECTION_FIELD_MAP.get(doc_type, {})

    # Ordered list of unique JSON field names following section order
    seen: set[str] = set()
    ordered_fields: list[str] = []
    for section in section_order:
        for f in mapping.get(section, []):
            if f not in seen:
                ordered_fields.append(f)
                seen.add(f)
    for f in sorted(_ALWAYS_ALLOWED):
        if f not in seen:
            ordered_fields.append(f)

    lines: list[str] = [
        "TEMPLATE CONTRACT (non-negotiable):",
        f"  Document type : {tmpl.get('display_name', doc_type)}",
        "",
        "  Allowed JSON keys — output ONLY these keys, no others:",
    ]
    for f in ordered_fields:
        lines.append(f"    • {f}")

    lines += ["", "  Section order, required status, and field mapping:"]
    for section in section_order:
        fields = mapping.get(section, [])
        req = "[REQUIRED]" if section in required_sections else "[optional]"
        field_str = (
            ", ".join(fields) if fields
            else "(no separate key — part of parent field)"
        )
        lines.append(f"    {req} {section}  →  {field_str}")

    lines += [
        "",
        "  Rules:",
        '    • Required string fields: output "Not provided" if source data is unavailable.',
        "    • Required list/table fields: output [] if source data is unavailable.",
        "    • Do NOT add JSON keys beyond those listed above.",
        "    • Do NOT invent facts; cite only from PROGRAM FACT-PACK and SOURCES.",
        "",
    ]
    return "\n".join(lines) + "\n"

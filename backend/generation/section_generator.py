"""
section_generator.py — One focused LLM call per document section.

Each call receives:
  - A compact system prompt (≤25 lines) specific to the section
  - A fact pack: only the facts that section needs
  - Retrieved chunks (hybrid search results)
  - An exemplar style excerpt (≤600 chars) if available
  - The section's JSON output schema

Returns a validated dict matching the section schema.
"""
import json
import logging
from typing import Any, Optional, Type

from pydantic import BaseModel

from llm.client import get_client as get_openai_client

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"
MAX_RETRIES = 2

# Resolved human directives for each DocModifier enum value.
# Used instead of raw enum strings so the LLM receives explicit instructions.
_MODIFIER_DIRECTIVES: dict[str, str] = {
    "EMPHASIZE_COMMERCIAL":          "Prioritize COTS/MOTS solutions; justify any custom development.",
    "INCLUDE_DO178_DO297":           "Address DO-178C software assurance and DO-297 IMA certification requirements.",
    "HW_SW_SEPARATION":              "Emphasize independent hardware/software upgrade paths.",
    "ATTRITABLE_LIFECYCLE":          "Use planned-obsolescence framing; address accelerated fielding lifecycle.",
    "MISSION_CRITICAL_VERIFICATION": "Emphasize V&V rigor commensurate with mission-critical classification.",
    "SUSTAINMENT_TAIL_PLANNING":     "Include long-term sustainment planning and technology refresh strategy.",
    "HIGH_TECH_RISK_MODULAR":        "Address elevated technical risk through modular decomposition and incremental development.",
    "COTS_REFRESH_CYCLE":            "Address COTS refresh cycles and second-source qualification strategy.",
    "REUSE_TYPE_ANALYSIS":           "Classify each module as adopt/adapt/extend based on similar program analysis.",
}

# Keys present in the fact_pack that are already surfaced in the system prompt.
# Removing them from the user-message context avoids double-sending.
_SYSTEM_PROMPT_KEYS = frozenset({"rule_violations", "modifiers"})


def _build_system_prompt(
    section_name: str,
    section_instructions: str,
    doc_type: str,
    modifiers: list[str],
    style_excerpt: Optional[str],
    rule_violations: Optional[list[dict]] = None,
) -> str:
    # Resolve modifier enum values to human directives; skip unknown values
    directive_lines = [
        _MODIFIER_DIRECTIVES[m] for m in modifiers if m in _MODIFIER_DIRECTIVES
    ]
    directive_block = ""
    if directive_lines:
        directive_block = "\nDirectives:\n" + "\n".join(f"- {d}" for d in directive_lines)

    # Only WARN/ERROR violations become prompt directives; INFO stays out of the prompt
    violations_block = ""
    if rule_violations:
        actionable = [v for v in rule_violations if v.get("severity") in ("ERROR", "WARN")]
        if actionable:
            lines = "\n".join(
                f"- [{v['severity']}] {v['message']}" for v in actionable
            )
            violations_block = f"\nFindings to address:\n{lines}"

    style_block = ""
    if style_excerpt:
        style_block = f"\nStyle reference:\n---\n{style_excerpt[:400]}\n---"

    doc_label = doc_type.upper().replace("_", " ")
    return (
        f"{doc_label} — {section_name}\n\n"
        f"{section_instructions}\n\n"
        f"Rules: JSON only · No invented facts · [ASSUMPTION: ...] if required field absent · Government English"
        f"{directive_block}{violations_block}{style_block}"
    )


def generate_section(
    *,
    section_name: str,
    section_instructions: str,
    doc_type: str,
    output_schema: Type[BaseModel],
    fact_pack: dict[str, Any],
    retrieved_chunks: list[str],
    modifiers: list[str],
    style_excerpt: Optional[str] = None,
    program_name: str = "the program",
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """
    Generate one section and return a validated dict.

    Raises ValueError if the LLM output cannot be parsed after MAX_RETRIES.
    """
    client = get_openai_client()

    # Pull rules data before building prompts
    rule_violations = fact_pack.get("rule_violations")

    system_prompt = _build_system_prompt(
        section_name, section_instructions, doc_type, modifiers, style_excerpt,
        rule_violations=rule_violations,
    )

    # Strip keys already promoted to the system prompt so they are not double-sent
    context_data = {k: v for k, v in fact_pack.items() if k not in _SYSTEM_PROMPT_KEYS}

    # Compact JSON (no indent) — exclude None values if the dict came from a Pydantic model
    fact_block = json.dumps(context_data, separators=(",", ":"), default=str)
    chunk_block = "\n---\n".join(retrieved_chunks[:6]) if retrieved_chunks else "(none)"
    schema_block = json.dumps(output_schema.model_json_schema(), indent=2)

    user_msg = (
        f"{program_name}\n"
        f"CONTEXT: {fact_block}\n"
        f"SOURCES: {chunk_block}\n"
        f"OUTPUT SCHEMA:\n{schema_block}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    last_error: Optional[Exception] = None
    raw: str = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=max_tokens,
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            validated = output_schema.model_validate(data)
            return validated.model_dump()

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Section '%s' attempt %d/%d failed: %s",
                section_name, attempt + 1, MAX_RETRIES + 1, exc,
            )
            if attempt < MAX_RETRIES:
                # Only include the prior assistant turn if we actually received one
                if raw:
                    messages.append({"role": "assistant", "content": raw})
                messages.append({
                    "role": "user",
                    "content": f"Output was invalid: {exc}. Correct the JSON and output only a valid object matching the schema.",
                })
                raw = ""  # reset for next attempt

    raise ValueError(f"Section '{section_name}' failed after {MAX_RETRIES + 1} attempts: {last_error}")

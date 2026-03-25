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

from llm.client import get_openai_client

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"
MAX_RETRIES = 2


def _build_system_prompt(
    section_name: str,
    section_instructions: str,
    doc_type: str,
    modifiers: list[str],
    style_excerpt: Optional[str],
) -> str:
    modifier_block = ""
    if modifiers:
        modifier_block = "\n\nACTIVE MODIFIERS — emphasize these themes:\n" + "\n".join(
            f"  - {m}" for m in modifiers
        )

    style_block = ""
    if style_excerpt:
        style_block = f"\n\nEXEMPLAR STYLE REFERENCE (match this tone and structure):\n---\n{style_excerpt[:600]}\n---"

    return f"""You are a DoD acquisition document writer producing the "{section_name}" section
of a {doc_type.upper().replace("_", " ")} document.

{section_instructions}

Rules:
- Use facts provided. Do not invent program names, costs, dates, or technical details.
- Insert [ASSUMPTION: ...] for any required field that has no factual basis.
- Output ONLY valid JSON matching the schema below. No markdown, no prose outside JSON.
- Be specific. Avoid boilerplate unless facts are unavailable.
- Use plain government English — no marketing language.
{modifier_block}{style_block}"""


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
) -> dict[str, Any]:
    """
    Generate one section and return a validated dict.

    Raises ValueError if the LLM output cannot be parsed after MAX_RETRIES.
    """
    client = get_openai_client()

    system_prompt = _build_system_prompt(
        section_name, section_instructions, doc_type, modifiers, style_excerpt
    )

    # Build user message
    fact_block = json.dumps(fact_pack, indent=2, default=str)
    chunk_block = "\n\n---\n\n".join(retrieved_chunks[:8]) if retrieved_chunks else "(none)"
    schema_block = json.dumps(output_schema.model_json_schema(), indent=2)

    user_msg = f"""PROGRAM: {program_name}

PROGRAM FACTS:
{fact_block}

RETRIEVED KNOWLEDGE (use for grounding, cite file_id when referencing):
{chunk_block}

OUTPUT JSON SCHEMA:
{schema_block}

Now generate the "{section_name}" section as a single JSON object matching the schema above."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2048,
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            # Validate against schema
            validated = output_schema.model_validate(data)
            return validated.model_dump()

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Section '%s' attempt %d/%d failed: %s",
                section_name, attempt + 1, MAX_RETRIES + 1, exc,
            )
            if attempt < MAX_RETRIES:
                messages.append({"role": "assistant", "content": raw if "raw" in dir() else ""})
                messages.append({
                    "role": "user",
                    "content": f"Your previous output was invalid: {exc}. Please output valid JSON matching the schema.",
                })

    raise ValueError(f"Section '{section_name}' failed after {MAX_RETRIES + 1} attempts: {last_error}")

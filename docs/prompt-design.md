# LLM Prompt Design Principles

This document captures the rules for writing and maintaining the prompts in
this codebase. Follow them when adding sections, modifying generation, or
debugging poor output quality.

---

## Core principle: short prompts, structured facts

Every LLM call in this app follows the same pattern:

```
[System]  ≤25 lines — role + rules + active modifiers + style excerpt
[User]    facts (JSON) + retrieved chunks + output schema + instruction
```

Never put facts in the system prompt. Never put role/rules in the user message.

---

## System prompt rules

### 1. State the role in one line

```
You are a DoD acquisition document writer producing the "Risk Register" section
of an ACQUISITION STRATEGY document.
```

Not: *"You are an expert AI assistant with deep knowledge of DoD acquisition
policy who has been trained on thousands of..."*

### 2. Give ≤5 writing rules

Focus on what would go wrong without the rule:

```
Rules:
- Use facts provided. Do not invent program names, costs, dates, or technical details.
- Insert [ASSUMPTION: ...] for any required field that has no factual basis.
- Output ONLY valid JSON matching the schema below. No markdown, no prose outside JSON.
- Be specific. Avoid boilerplate unless facts are unavailable.
- Use plain government English — no marketing language.
```

### 3. Active modifiers block (auto-generated)

Modifiers come from the rules engine — don't hardcode them. The section generator
appends them automatically:

```
ACTIVE MODIFIERS — emphasize these themes:
  - INCLUDE_DO178_DO297
  - HW_SW_SEPARATION
```

Write modifier names so they're self-describing to the LLM without needing
additional explanation.

### 4. Exemplar style excerpt (≤600 chars, optional)

```
EXEMPLAR STYLE REFERENCE (match this tone and structure):
---
[excerpt]
---
```

Cap strictly at 600 characters. Style injection is for tone, not facts.
Never let exemplar content override the fact pack.

### 5. No filler

Do not include:
- Motivational framing ("Your task is very important...")
- Redundant reminders ("Remember to be accurate...")
- Apology hedges ("If you're unsure, try your best...")

---

## Fact pack rules

### Include only what the section needs

Each `SectionDef` has a `fact_keys` list. The orchestrator slices the full
fact pack to only those keys. Keep the slice small — irrelevant facts
dilute attention and increase cost.

**Good `fact_keys` for a risk section:**
```python
fact_keys=["modules", "modifiers", "mission_critical", "safety_critical"]
```

**Bad (too broad):**
```python
fact_keys=list(full_facts.keys())  # sends everything
```

### Use JSON for structured facts

Pass modules, scenarios, and standards as JSON objects, not prose:

```json
{
  "modules": [
    {"name": "Navigation", "tech_risk": true, "cots_candidate": false},
    {"name": "Mission Computer", "tech_risk": false, "cots_candidate": true}
  ]
}
```

The LLM handles structured data more reliably than prose summaries of the same information.

### Mark unknown fields explicitly

Use Python's `None` → JSON `null` for missing facts. The prompt rule
"Insert [ASSUMPTION: ...] for any required field that has no factual basis"
then fires correctly.

Don't fill nulls with empty strings — the LLM will treat `""` as real data.

---

## Output schema rules

### One schema per section, not one schema per document

Each section has its own small Pydantic model. The LLM's full attention
goes to producing 3–8 fields, not 40+.

```python
class AcqRiskSection(BaseModel):
    risks: List[dict]   # [{risk_id, description, probability, impact, mitigation, owner}]
```

### Keep schemas flat

Avoid deeply nested models in section schemas. The LLM struggles with
3+ levels of nesting. Flatten to `List[dict]` with documented keys and
validate the inner structure post-call if needed.

### Always use `response_format: {"type": "json_object"}`

This eliminates markdown fences and prose preambles from output.
Never parse a free-text response — always use structured output.

### Retry once on schema failure

`section_generator.py` retries with the validation error message appended:
```
Your previous output was invalid: [error]. Please output valid JSON matching the schema.
```

Two attempts is the limit. On second failure, surface the error — don't
silently produce garbage.

---

## Retrieved chunks rules

### Cap at 8 chunks per section

Beyond 8 chunks, the context budget fills with marginally relevant content.
`section_generator.py` enforces this: `retrieved_chunks[:8]`.

### Separate facts from style

Don't mix program-specific retrieved chunks with exemplar style excerpts in
the same context position. The orchestrator keeps them separate:
- Chunks → `retrieved_chunks` parameter (grounding)
- Exemplar → `style_excerpt` parameter (tone only)

---

## Calibrating output quality

If a section produces poor output, debug in this order:

1. **Wrong facts**: Print the fact pack. Is the relevant data actually present?
2. **Missing chunks**: Print retrieved chunks. Is the relevant knowledge being retrieved?
3. **Prompt too vague**: Tighten the `instructions` string in the `SectionDef`
4. **Schema too loose**: Add more specific fields to the section schema
5. **Wrong model**: `gpt-4o-mini` is fast/cheap; switch to `gpt-4o` for complex sections

### Token budget per document

| Doc type | Sections | Avg tokens/section | Total |
|----------|----------|--------------------|-------|
| RFI | 4 | ~800 | ~3,200 |
| Acq Strategy | 6 | ~1,000 | ~6,000 |
| SEP | 4 | ~900 | ~3,600 |
| MCP | 3 | ~900 | ~2,700 |

Stay under 2,048 output tokens per section (`max_tokens=2048` in `section_generator.py`).
If sections are truncating, split them or reduce the schema's field count.

---

## What not to do

| Don't | Do instead |
|-------|-----------|
| Put policy text verbatim in prompts | Put it in `reference_docs/` and retrieve it |
| Hardcode program names in prompts | Pass via fact pack |
| Write 50-line system prompts | ≤25 lines, trim ruthlessly |
| Use one prompt for the whole document | One focused prompt per section |
| Retry more than once on failure | Surface the error to the user |
| Use temperature > 0.5 | Keep at 0.3 for factual consistency |

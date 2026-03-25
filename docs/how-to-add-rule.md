# How to Add a Rule

Rules are deterministic — no LLM calls. They take program facts as input and
produce modifiers, violations, and flags that downstream document generation
uses to adjust its prompts and content.

---

## The rules pipeline

```
RulesInput (dataclass)
    ↓
evaluate_rules()          ← backend/rules/engine.py
    ↓
RulesResult
  .mig_id                 — auto-selected Modular Implementation Guide
  .modifiers              — DocModifier flags → injected into LLM system prompts
  .violations             — ERROR / WARN / INFO findings → shown in SufficiencyBanner
  .flags                  — arbitrary boolean flags for orchestrator logic
```

`evaluate_rules()` is called in two places:
- `GET /programs/{id}/sufficiency` (shown in UI)
- `generation/orchestrator.py` before each document generation run

---

## Step 1 — Add the input field (if needed)

If your rule needs a fact that `RulesInput` doesn't already have, add it:

**File:** `backend/rules/models.py`

```python
@dataclass
class RulesInput:
    # ... existing fields ...
    your_new_field: Optional[bool] = None
```

Then populate it in the two callers:

**`backend/routers/sufficiency.py`** — in `get_sufficiency()`:
```python
rules_inp = RulesInput(
    ...
    your_new_field=brief.get("your_new_field"),
)
```

**`backend/generation/orchestrator.py`** — in `generate_document()`:
```python
rules_inp = RulesInput(
    ...
    your_new_field=getattr(brief, "your_new_field", None) if brief else None,
)
```

---

## Step 2 — Add a DocModifier (if needed)

If your rule should change document tone or content, add a modifier:

**File:** `backend/rules/models.py`

```python
class DocModifier(str, Enum):
    # ... existing modifiers ...
    YOUR_NEW_MODIFIER = "YOUR_NEW_MODIFIER"
```

---

## Step 3 — Write the rule

**File:** `backend/rules/engine.py`

Add a numbered block in `evaluate_rules()`:

```python
# Rule N — your rule description
if inp.your_new_field:
    result.modifiers.append(DocModifier.YOUR_NEW_MODIFIER)
    violations.append(RuleViolation(
        rule_id="YOUR_RULE_ID",
        severity="WARN",          # ERROR | WARN | INFO
        message="Human-readable message shown in the UI.",
        field="your_new_field",   # optional — highlights the relevant field
    ))
    result.flags["your_flag"] = True
```

### Severity levels

| Level | Shown as | Blocks generation? |
|-------|---------|-------------------|
| `ERROR` | Red gate failure | Yes (if wired to a gate) |
| `WARN` | Yellow warning pill | No |
| `INFO` | Gray info pill | No |

---

## Step 4 — Wire the modifier into prompts (if needed)

**File:** `backend/generation/section_generator.py`

Modifiers are already injected automatically via the `ACTIVE MODIFIERS` block
in `_build_system_prompt()`. No changes needed for new modifiers.

To add specific language for your modifier in a particular section, edit the
section's `instructions` string in `backend/generation/orchestrator.py`:

```python
SectionDef(
    name="Contracting Strategy",
    instructions="""Describe contracting vehicle...
If YOUR_NEW_MODIFIER is active: emphasize [specific requirement].""",
    ...
)
```

---

## Step 5 — Test it

```python
# Quick smoke test in the Python REPL:
cd backend && source .venv/bin/activate && python

from rules.engine import evaluate_rules
from rules.models import RulesInput

result = evaluate_rules(RulesInput(your_new_field=True, module_count=3))
print(result.modifiers)
print(result.violations)
```

---

## Rules checklist

- [ ] Rule has a unique `rule_id` string (SCREAMING_SNAKE_CASE)
- [ ] Severity is appropriate (`INFO` for informational, `WARN` for actionable, `ERROR` for blocking)
- [ ] Message is a complete sentence, PM-readable (no jargon abbreviations unexplained)
- [ ] New `DocModifier` value matches what you reference in `evaluate_rules()`
- [ ] Both callers (`sufficiency.py` and `orchestrator.py`) populate the new `RulesInput` field

# How to Add a Wizard Question

Wizard questions are defined in one file and stored in one database table.
No migrations required for adding questions.

---

## Step 1 — Add the question to `questions.yaml`

**File:** `backend/config/questions.yaml`

```yaml
questions:
  # ... existing questions ...

  - id: p_your_new_question          # must be unique; prefix with a letter + underscore
    prompt: "Your question text?"
    help: "Longer helper text shown below the field."
    type: textarea                    # see types below
```

### Question types

| Type | Renders as | Notes |
|------|-----------|-------|
| `textarea` | Multi-line text area | Most common |
| `number` | Number input | Value stored as string |
| `select` | Radio button group | Requires `options:` list |
| `modules_builder` | Inline row table | Reserved for `h_candidate_modules` |

For `select`, add an `options` list:
```yaml
  - id: p_your_select
    prompt: "Which applies?"
    help: "Select the best fit."
    type: select
    options:
      - value: option_a
        label: Option A
      - value: option_b
        label: Option B
```

---

## Step 2 — No backend code changes needed

`_load_questions()` in `main.py` reads `questions.yaml` at request time.
The wizard PUT endpoint (`/programs/{id}/wizard`) automatically accepts
any key in the YAML `id` list.

Restart the backend after editing the YAML:
```bash
# dev server auto-reloads on file changes; or:
uvicorn main:app --reload
```

---

## Step 3 — Wire up the frontend

Wizard answers are stored as flat key-value pairs. The frontend reads them
via `GET /programs/{id}/wizard` which returns:
```json
{
  "answers": { "p_your_new_question": "..." },
  "questions": [{ "id": "p_your_new_question", "prompt": "...", ... }]
}
```

**Option A — generic rendering** (zero frontend work): The wizard will
automatically include the new question if the frontend has a generic
question renderer. Check `BriefTab.tsx` for the `wizardAnswers` map —
any `textarea` question can be added as a new `form-card` block.

**Option B — explicit field** in `BriefTab.tsx`:
```tsx
<div className="form-card">
  <div className="form-card__header">
    <h3 className="form-card__title">Your Section Title</h3>
  </div>
  <div className="form-card__body">
    <div className="form-field">
      <textarea
        rows={4}
        value={wizardAnswers['p_your_new_question'] ?? ''}
        onChange={e => handleWizardText('p_your_new_question', e.target.value)}
        placeholder="Describe…"
      />
    </div>
  </div>
</div>
```

---

## Step 4 — Use the answer in document generation (optional)

If the answer should feed into generated documents, add the question ID
to `required_fields` in `document_templates.py`:

```python
# backend/document_templates.py
"rfi": {
    ...
    "required_fields": [
        "a_program_description",
        "g_mosa_scenarios",
        "p_your_new_question",   # add here
    ],
}
```

Then reference it in the relevant LLM section's fact pack in
`generation/orchestrator.py` → `_build_full_fact_pack()`:

```python
"your_field": wizard_answers.get("p_your_new_question"),
```

---

## Naming convention

Question IDs use a single letter prefix indicating approximate order:
`a_` through `o_` are taken. Use `p_` through `z_` for new questions.
Keep IDs stable — changing an ID orphans existing saved answers.

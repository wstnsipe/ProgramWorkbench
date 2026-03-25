# How to Add a New Document Type

Adding a document type touches five files. Work through them in order.

Existing types for reference: `rfi`, `acq_strategy`, `sep`, `mcp`.

---

## 1. Register the template

**File:** `backend/document_templates.py`

Add an entry to `TEMPLATE_REGISTRY`:

```python
TEMPLATE_REGISTRY["your_doc_type"] = {
    "display_name": "Your Document Type (YDT)",
    "section_order": [
        "1. Introduction",
        "2. Background",
        "3. Your Main Section",
        "Appendix A: Sources Used",
    ],
    "required_sections": [
        "1. Introduction",
        "2. Background",
        "3. Your Main Section",
    ],
    "section_format": {
        "1. Introduction":       "narrative",
        "2. Background":         "narrative",
        "3. Your Main Section":  "mixed",
        "Appendix A: Sources Used": "bullet",
    },
    "required_fields": [
        "a_program_description",   # wizard answer keys that must be present
        "g_mosa_scenarios",
    ],
}
```

### Section format values
- `"narrative"` — flowing prose
- `"bullet"` — bulleted list
- `"mixed"` — prose intro + bullets or table
- `"table"` — structured tabular data

---

## 2. Add section schemas

**File:** `backend/generation/section_schemas.py`

Add a Pydantic output schema for each section:

```python
class YdtIntroSection(BaseModel):
    introduction: str
    scope: str

class YdtBackgroundSection(BaseModel):
    background: str
    context_bullets: List[str]

class YdtMainSection(BaseModel):
    main_content: str
    supporting_points: List[str]
```

---

## 3. Add section definitions to the orchestrator

**File:** `backend/generation/orchestrator.py`

Import your schemas and add a section list:

```python
from generation.section_schemas import YdtIntroSection, YdtBackgroundSection, YdtMainSection

_YDT_SECTIONS: list[SectionDef] = [
    SectionDef(
        name="Introduction",
        schema_class=YdtIntroSection,
        instructions="Write a 2-3 paragraph introduction covering purpose and scope.",
        fact_keys=["program_name", "program_description", "service_branch"],
        exemplar_pattern="introduction",
    ),
    SectionDef(
        name="Background",
        schema_class=YdtBackgroundSection,
        instructions="Summarize program background and 3-5 context bullets.",
        fact_keys=["program_description", "dev_cost_estimate", "timeline_months"],
        exemplar_pattern="background",
    ),
    SectionDef(
        name="Your Main Section",
        schema_class=YdtMainSection,
        instructions="Write the main section content grounded in program facts.",
        fact_keys=["modules", "standards", "modifiers"],
        exemplar_pattern="main",
    ),
]

# Add to SECTION_MAP
SECTION_MAP: dict[str, list[SectionDef]] = {
    "rfi":           _RFI_SECTIONS,
    "acq_strategy":  _ACQ_STRATEGY_SECTIONS,
    "sep":           _SEP_SECTIONS,
    "mcp":           _MCP_SECTIONS,
    "your_doc_type": _YDT_SECTIONS,    # ← add this
}
```

---

## 4. Add the DOCX renderer

**File:** `backend/generation/renderer.py`

Add your doc type to `_BUILDER_FN_MAP`:

```python
_BUILDER_FN_MAP = {
    "rfi":           "build_rfi_docx",
    "acq_strategy":  "build_acq_strategy_docx",
    "sep":           "build_sep_docx",
    "mcp":           "build_mcp_docx",
    "your_doc_type": "build_your_doc_type_docx",   # ← add this
}
```

Then add the builder function in `backend/docx_builder.py`.
The simplest approach is to copy an existing builder (e.g., `build_rfi_docx`)
and adapt the section rendering. Each section key in `assembled` matches
the `SectionDef.name` strings defined in step 3.

---

## 5. Add the doc type to frontend schemas

**File:** `frontend/src/types/index.ts`

```typescript
export type DocType = 'rfi' | 'acq_strategy' | 'sep' | 'mcp' | 'your_doc_type'
```

**File:** `frontend/src/schemas_v2.py` (backend, for FastAPI validation):

```python
class DocType(str, Enum):
    RFI = "rfi"
    ACQ_STRATEGY = "acq_strategy"
    SEP = "sep"
    MCP = "mcp"
    YOUR_DOC_TYPE = "your_doc_type"
```

Add a button in `frontend/src/pages/DocumentsTab.tsx`:

```tsx
<button onClick={() => handleGenerate('your_doc_type')}>
  Generate Your Document Type
</button>
```

---

## Checklist

- [ ] `TEMPLATE_REGISTRY` entry with `display_name`, `section_order`, `required_sections`, `section_format`, `required_fields`
- [ ] Pydantic section schemas in `section_schemas.py`
- [ ] `SectionDef` list and `SECTION_MAP` entry in `orchestrator.py`
- [ ] Builder function name in `renderer.py` `_BUILDER_FN_MAP`
- [ ] `build_your_doc_type_docx()` function in `docx_builder.py`
- [ ] `DocType` enum updated in both `frontend/src/types/index.ts` and `backend/schemas_v2.py`
- [ ] UI button in `DocumentsTab.tsx`

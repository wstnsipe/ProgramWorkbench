# APW API Contracts

Single reference for every endpoint's request/response shape, plus JSON schemas for
sufficiency, rules, and document generation payloads.

---

## Canonical field naming rules

| Rule | Example |
|------|---------|
| All fields `snake_case` | `program_description`, `dev_cost_estimate` |
| Timestamps as ISO-8601 strings on the wire | `"2025-01-15T12:00:00"` |
| Nullable optional fields omit the key or send `null` | `"army_pae": null` |
| Enum values are lowercase strings | `"rfi"`, `"usn"`, `"reprocure"` |
| Booleans never as `0/1` | `true` / `false` |
| Numeric IDs as integers | `"program_id": 42` |
| Bulk-replace payloads wrap the list in a named key | `{"modules": [...]}` |
| Input schemas → `<Resource>In` / `<Resource>sBulkIn` | `ModuleIn`, `ModulesBulkIn` |
| Output schemas → `<Resource>Out` | `ModuleOut`, `SufficiencyOut` |

All schemas live in `backend/contracts.py` (Python) and `frontend/src/types/index.ts` (TypeScript).

---

## Programs

### `POST /programs`
Create a program.

**Request**
```json
{
  "name": "NCOW-M",
  "service_branch": "ARMY",
  "army_pae": "PA-001"
}
```

**Response** `201`
```json
{
  "id": 1,
  "name": "NCOW-M",
  "service_branch": "ARMY",
  "army_pae": "PA-001",
  "mig_id": null
}
```

---

### `GET /programs/{id}`
**Response** `200` — same shape as POST response.

---

### `PATCH /programs/{id}`
Partial update. All fields optional.

**Request**
```json
{
  "service_branch": "USN"
}
```
**Response** `200` — full `ProgramOut`.

---

## Brief

### `GET /programs/{id}/brief`
**Response** `200`
```json
{
  "program_id": 1,
  "program_description": "Network-Centric Operations Widget...",
  "dev_cost_estimate": 125000000.0,
  "production_unit_cost": 8500.0,
  "timeline_months": 36,
  "attritable": false,
  "sustainment_tail": true,
  "software_large_part": true,
  "software_involved": true,
  "mission_critical": true,
  "safety_critical": false,
  "similar_programs_exist": true,
  "updated_at": "2025-01-15T12:00:00"
}
```

---

### `PUT /programs/{id}/brief`
Full upsert. All fields optional — only sent fields are updated.

**Request** — any subset of BriefIn fields:
```json
{
  "program_description": "Network-Centric Operations Widget...",
  "dev_cost_estimate": 125000000.0,
  "timeline_months": 36,
  "mission_critical": true
}
```
**Response** `200` — full `BriefOut`.

---

## Modules

### `GET /programs/{id}/modules`
**Response** `200` — array of `ModuleOut`
```json
[
  {
    "id": 10,
    "program_id": 1,
    "name": "Navigation",
    "description": "Inertial navigation subsystem",
    "rationale": "Mission-critical; isolated for recompete",
    "key_interfaces": "MIL-STD-1553, ARINC 429",
    "standards": "DO-178C Level A",
    "tech_risk": false,
    "obsolescence_risk": true,
    "cots_candidate": false,
    "future_recompete": true,
    "created_at": "2025-01-10T08:00:00"
  }
]
```

---

### `PUT /programs/{id}/modules`
Replace ALL modules atomically. Rows with blank `name` are silently dropped.

**Request**
```json
{
  "modules": [
    {
      "name": "Navigation",
      "description": "Inertial navigation subsystem",
      "rationale": "Mission-critical; isolated for recompete",
      "key_interfaces": "MIL-STD-1553, ARINC 429",
      "standards": "DO-178C Level A",
      "tech_risk": false,
      "obsolescence_risk": true,
      "cots_candidate": false,
      "future_recompete": true
    }
  ]
}
```
**Response** `200` — array of `ModuleOut`.

---

### `DELETE /programs/{id}/modules/{module_id}`
**Response** `204`

---

## MOSA Scenarios

### `GET /programs/{id}/scenarios`
**Response** `200` — array of `ScenarioOut`
```json
[
  {
    "id": 5,
    "program_id": 1,
    "scenario_type": "reprocure",
    "module_name": "Navigation",
    "description": "Government solicits competing vendors using published ICD...",
    "word_count": 47,
    "created_at": "2025-01-10T08:00:00",
    "updated_at": "2025-01-10T08:00:00"
  }
]
```

---

### `PUT /programs/{id}/scenarios`
Replace ALL scenarios atomically. `word_count` is computed server-side.

**Request**
```json
{
  "scenarios": [
    {
      "scenario_type": "reprocure",
      "module_name": "Navigation",
      "description": "Government solicits competing vendors using published ICD..."
    },
    {
      "scenario_type": "reuse",
      "module_name": "Comms",
      "description": "Comms module reused from AEHF program with updated firmware..."
    }
  ]
}
```
**Response** `200` — array of `ScenarioOut`.

`scenario_type` enum: `"reprocure"` | `"reuse"` | `"recompete"`

---

## Standards

### `GET /programs/{id}/standards`
**Response** `200` — array of `StandardOut`
```json
[
  {
    "id": 3,
    "program_id": 1,
    "standard_name": "FACE Technical Standard",
    "applies": true,
    "catalog_id": "FACE",
    "notes": "Applies to all software-intensive modules",
    "created_at": "2025-01-10T08:00:00"
  }
]
```

---

### `PUT /programs/{id}/standards`
Replace ALL standards atomically.

**Request**
```json
{
  "standards": [
    {
      "standard_name": "FACE Technical Standard",
      "applies": true,
      "catalog_id": "FACE",
      "notes": "Applies to all software-intensive modules"
    },
    {
      "standard_name": "DO-178C",
      "applies": false,
      "catalog_id": "DO178C",
      "notes": null
    }
  ]
}
```
**Response** `200` — array of `StandardOut`.

---

## Sufficiency

### `GET /programs/{id}/sufficiency`
Pure deterministic scoring. No LLM. Always fresh — not cached.

**Response** `200`

```json
{
  "level": "YELLOW_HIGH",
  "score": 72.0,
  "gates": [
    { "gate_id": "PROGRAM_NAME",   "passed": true,  "message": "Program name must be set" },
    { "gate_id": "DESCRIPTION",    "passed": true,  "message": "Program description must be set" },
    { "gate_id": "SERVICE_BRANCH", "passed": true,  "message": "Service branch must be selected" },
    { "gate_id": "MODULES_EXIST",  "passed": true,  "message": "At least one module must be defined" }
  ],
  "coverage": [
    { "field_id": "program_description",  "label": "Program Description", "weight": 15.0, "present": true,  "source": "brief" },
    { "field_id": "service_branch",       "label": "Service Branch",       "weight": 8.0,  "present": true,  "source": "program" },
    { "field_id": "dev_cost_estimate",    "label": "Dev Cost Estimate",    "weight": 7.0,  "present": true,  "source": "brief" },
    { "field_id": "production_unit_cost", "label": "Production Unit Cost", "weight": 5.0,  "present": false, "source": "brief" },
    { "field_id": "timeline_months",      "label": "Timeline (months)",    "weight": 6.0,  "present": true,  "source": "brief" },
    { "field_id": "attritable",           "label": "Attritable Flag",      "weight": 4.0,  "present": true,  "source": "brief" },
    { "field_id": "mission_critical",     "label": "Mission Critical",     "weight": 4.0,  "present": true,  "source": "brief" },
    { "field_id": "safety_critical",      "label": "Safety Critical",      "weight": 4.0,  "present": true,  "source": "brief" },
    { "field_id": "software_large_part",  "label": "Software Dominant",    "weight": 3.0,  "present": true,  "source": "brief" },
    { "field_id": "modules_defined",      "label": "Modules Defined",      "weight": 20.0, "present": true,  "source": "module" },
    { "field_id": "scenarios_defined",    "label": "MOSA Scenarios (≥2)",  "weight": 12.0, "present": false, "source": "wizard" },
    { "field_id": "standards_defined",    "label": "Standards Identified", "weight": 7.0,  "present": false, "source": "standard" },
    { "field_id": "files_uploaded",       "label": "Supporting Files",     "weight": 5.0,  "present": false, "source": "file" }
  ],
  "missing_critical": ["MOSA Scenarios (≥2)"],
  "warnings": ["Production Unit Cost", "Timeline (months)", "Standards Identified", "Supporting Files"],
  "mig_id": "MIG-ARMY-SW",
  "modifiers": ["HW_SW_SEPARATION", "EMPHASIZE_COMMERCIAL"],
  "rule_violations": [
    {
      "rule_id": "RULE_07",
      "severity": "WARN",
      "message": "ARMY programs with software > 50% should evaluate DO-178C or FACE compliance"
    }
  ]
}
```

**Level thresholds**

| Level | Condition |
|-------|-----------|
| `RED` | Any gate failed |
| `YELLOW_LOW` | All gates pass, score < 55 |
| `YELLOW_HIGH` | All gates pass, 55 ≤ score < 80 |
| `GREEN` | All gates pass, score ≥ 80 |

**Coverage weights** (sum = 100)

| field_id | weight | source |
|----------|--------|--------|
| `program_description` | 15 | brief |
| `modules_defined` | 20 | module |
| `scenarios_defined` | 12 | wizard |
| `service_branch` | 8 | program |
| `dev_cost_estimate` | 7 | brief |
| `standards_defined` | 7 | standard |
| `timeline_months` | 6 | brief |
| `files_uploaded` | 5 | file |
| `production_unit_cost` | 5 | brief |
| `attritable` | 4 | brief |
| `mission_critical` | 4 | brief |
| `safety_critical` | 4 | brief |
| `software_large_part` | 3 | brief |

**`missing_critical`** — labels of fields with `weight ≥ 8` that are not present.
**`warnings`** — labels of fields with `4 ≤ weight < 8` that are not present.

---

## Files

### `POST /programs/{id}/files`
Multipart upload. `source_type` query param: `"program_input"` (default) | `"exemplar"`.

**Response** `201` — array of `FileOut`
```json
[
  {
    "id": 7,
    "program_id": 1,
    "filename": "ICD-Nav-v3.pdf",
    "relative_path": "1/ICD-Nav-v3.pdf",
    "size_bytes": 204800,
    "uploaded_at": "2025-01-15T12:00:00",
    "extracted_text": null,
    "source_type": "program_input"
  }
]
```

---

### `POST /programs/{id}/files/{file_id}/extract`
Trigger text extraction and chunking. Idempotent.

**Response** `200`
```json
{
  "file_id": 7,
  "filename": "ICD-Nav-v3.pdf",
  "chars_extracted": 18420,
  "chunks_created": 37,
  "error": null
}
```

---

### `DELETE /programs/{id}/files/{file_id}`
**Response** `204`

---

## Documents

### `GET /programs/{id}/documents`
**Response** `200` — array of `DocumentOut`
```json
[
  {
    "id": 2,
    "program_id": 1,
    "doc_type": "rfi",
    "file_path": "data/documents/1/rfi_abc123.docx",
    "created_at": "2025-01-15T14:30:00"
  }
]
```

---

### `POST /programs/{id}/documents/generate`
Queues async generation. Returns immediately. Blocked if sufficiency level is `RED`.

**Request**
```json
{
  "doc_type": "rfi",
  "force": false
}
```
`doc_type` enum: `"rfi"` | `"acq_strategy"` | `"sep"` | `"mcp"`

**Response** `202`
```json
{
  "job_id": "f4a1b2c3-...",
  "status": "queued",
  "doc_type": "rfi",
  "program_id": 1,
  "document_id": null,
  "download_url": null,
  "error": null
}
```

**Error** `422` — sufficiency RED:
```json
{
  "detail": "Sufficiency check failed — resolve RED issues before generating.",
  "gates_failed": ["Program description must be set"]
}
```

**`status`** enum: `"queued"` | `"generating"` | `"done"` | `"error"`

When `status == "done"`: `document_id` is set, `download_url` is populated.

---

### `GET /programs/{id}/documents/{document_id}/download`
Streams the `.docx` file.
`Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`

---

## Wizard

### `GET /programs/{id}/wizard`
**Response** `200`
```json
{
  "questions": [
    {
      "id": "g_acquisition_history",
      "prompt": "Describe any prior acquisition history for this program or similar systems.",
      "help": "Include prior contract vehicles, predecessor programs, or related efforts.",
      "type": "textarea",
      "options": null,
      "missing": true
    }
  ],
  "answers": {
    "g_acquisition_history": "No prior contracts. First-generation effort."
  },
  "answered_count": 1,
  "total_count": 6,
  "percent_complete": 16.7
}
```

---

### `PUT /programs/{id}/wizard`
Partial upsert — only keys in `answers` are written.

**Request**
```json
{
  "answers": {
    "g_acquisition_history": "No prior contracts. First-generation effort.",
    "g_competitive_landscape": "Three known vendors with relevant COTS."
  }
}
```
**Response** `204`

---

## JSON Schema: Sufficiency Result

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SufficiencyOut",
  "type": "object",
  "required": ["level", "score", "gates", "coverage", "missing_critical", "warnings"],
  "properties": {
    "level":            { "type": "string", "enum": ["GREEN", "YELLOW_HIGH", "YELLOW_LOW", "RED"] },
    "score":            { "type": "number", "minimum": 0, "maximum": 100 },
    "gates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["gate_id", "passed", "message"],
        "properties": {
          "gate_id": { "type": "string" },
          "passed":  { "type": "boolean" },
          "message": { "type": "string" }
        }
      }
    },
    "coverage": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["field_id", "label", "weight", "present", "source"],
        "properties": {
          "field_id": { "type": "string" },
          "label":    { "type": "string" },
          "weight":   { "type": "number" },
          "present":  { "type": "boolean" },
          "source":   { "type": "string", "enum": ["brief", "program", "module", "wizard", "standard", "file"] }
        }
      }
    },
    "missing_critical": { "type": "array", "items": { "type": "string" } },
    "warnings":         { "type": "array", "items": { "type": "string" } },
    "mig_id":           { "type": ["string", "null"] },
    "modifiers":        { "type": "array", "items": { "type": "string" } },
    "rule_violations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["rule_id", "severity", "message"],
        "properties": {
          "rule_id":  { "type": "string" },
          "severity": { "type": "string", "enum": ["ERROR", "WARN", "INFO"] },
          "message":  { "type": "string" }
        }
      }
    }
  }
}
```

---

## JSON Schema: Rules Engine Output

The rules engine runs inside `sufficiency_service.py` and its output is embedded in `SufficiencyOut`.
Standalone shape (from `backend/rules/models.py`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RulesResult",
  "type": "object",
  "required": ["mig_id", "modifiers", "violations"],
  "properties": {
    "mig_id": {
      "type": ["string", "null"],
      "description": "Matched MIG identifier, e.g. MIG-ARMY-SW, MIG-USN-HW"
    },
    "modifiers": {
      "type": "array",
      "description": "DocModifier enum values to inject into generation prompts",
      "items": {
        "type": "string",
        "enum": [
          "INCLUDE_DO178_DO297",
          "HW_SW_SEPARATION",
          "EMPHASIZE_COMMERCIAL",
          "REQUIRE_OPEN_STANDARDS",
          "FLAG_TECH_RISK",
          "FLAG_OBSOLESCENCE",
          "SUSTAINMENT_FOCUS",
          "ARMY_PAE_SECTION",
          "SHORT_ATTRITABLE_LIFECYCLE"
        ]
      }
    },
    "violations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["rule_id", "severity", "message"],
        "properties": {
          "rule_id":  { "type": "string", "pattern": "^RULE_\\d{2}$" },
          "severity": { "type": "string", "enum": ["ERROR", "WARN", "INFO"] },
          "message":  { "type": "string" }
        }
      }
    }
  }
}
```

**DocModifier → prompt effect**

| Modifier | Effect |
|----------|--------|
| `INCLUDE_DO178_DO297` | Add DO-178C / DO-297 section |
| `HW_SW_SEPARATION` | Emphasize hardware/software boundary in MOSA |
| `EMPHASIZE_COMMERCIAL` | Prioritize COTS/open-market approaches |
| `REQUIRE_OPEN_STANDARDS` | Mandate open standard justification |
| `FLAG_TECH_RISK` | Insert tech risk mitigation section |
| `FLAG_OBSOLESCENCE` | Insert obsolescence management section |
| `SUSTAINMENT_FOCUS` | Expand sustainment/logistics sections |
| `ARMY_PAE_SECTION` | Include Army PAE-specific guidance |
| `SHORT_ATTRITABLE_LIFECYCLE` | Shorten lifecycle language for attritable systems |

---

## JSON Schema: Document Generation Input

What `generate_document()` in `generation/orchestrator.py` receives internally.
This is the "assembled fact pack" shape, not an API payload.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GenerationInput",
  "type": "object",
  "required": ["program", "doc_type", "modifiers"],
  "properties": {
    "program": {
      "type": "object",
      "properties": {
        "id":             { "type": "integer" },
        "name":           { "type": "string" },
        "service_branch": { "type": ["string", "null"] },
        "army_pae":       { "type": ["string", "null"] },
        "mig_id":         { "type": ["string", "null"] }
      }
    },
    "doc_type": {
      "type": "string",
      "enum": ["rfi", "acq_strategy", "sep", "mcp"]
    },
    "brief": {
      "type": ["object", "null"],
      "properties": {
        "program_description":  { "type": ["string", "null"] },
        "dev_cost_estimate":    { "type": ["number", "null"] },
        "production_unit_cost": { "type": ["number", "null"] },
        "timeline_months":      { "type": ["integer", "null"] },
        "attritable":           { "type": ["boolean", "null"] },
        "sustainment_tail":     { "type": ["boolean", "null"] },
        "software_large_part":  { "type": ["boolean", "null"] },
        "software_involved":    { "type": ["boolean", "null"] },
        "mission_critical":     { "type": ["boolean", "null"] },
        "safety_critical":      { "type": ["boolean", "null"] },
        "similar_programs_exist": { "type": ["boolean", "null"] }
      }
    },
    "modules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name":               { "type": "string" },
          "description":        { "type": ["string", "null"] },
          "rationale":          { "type": ["string", "null"] },
          "key_interfaces":     { "type": ["string", "null"] },
          "standards":          { "type": ["string", "null"] },
          "tech_risk":          { "type": "boolean" },
          "obsolescence_risk":  { "type": "boolean" },
          "cots_candidate":     { "type": "boolean" },
          "future_recompete":   { "type": "boolean" }
        }
      }
    },
    "scenarios": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["scenario_type"],
        "properties": {
          "scenario_type": { "type": "string", "enum": ["reprocure", "reuse", "recompete"] },
          "module_name":   { "type": ["string", "null"] },
          "description":   { "type": ["string", "null"] },
          "word_count":    { "type": ["integer", "null"] }
        }
      }
    },
    "standards": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["standard_name", "applies"],
        "properties": {
          "standard_name": { "type": "string" },
          "applies":       { "type": "boolean" },
          "catalog_id":    { "type": ["string", "null"] },
          "notes":         { "type": ["string", "null"] }
        }
      }
    },
    "wizard_answers": {
      "type": "object",
      "description": "Free-text answers keyed by question_id",
      "additionalProperties": { "type": ["string", "null"] }
    },
    "modifiers": {
      "type": "array",
      "description": "DocModifier values from rules engine",
      "items": { "type": "string" }
    },
    "retrieved_chunks": {
      "type": "object",
      "description": "Top-8 pgvector chunks per section_id",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "chunk_id":  { "type": "integer" },
            "text":      { "type": "string" },
            "score":     { "type": "number" },
            "filename":  { "type": "string" }
          }
        }
      }
    }
  }
}
```

---

## Versioning notes

- **Current version**: All endpoints are unversioned (no `/v1` prefix in the v2 app).
- **Legacy `/v1`**: `main.py` is mounted at `/v1` in `main_v2.py` for backward compatibility. New clients use `main_v2.py` routes only.
- **`contracts.py`**: Single schema file going forward. `schemas.py` and `schemas_v2.py` remain for legacy routes but should not be extended.
- **Additive changes**: New optional fields on output schemas are non-breaking. Add `Optional[T] = None`.
- **Breaking changes**: Renaming fields or removing required fields requires a new path prefix (e.g., `/v3/programs`).
- **TypeScript sync**: After any change to `contracts.py`, update `frontend/src/types/index.ts` to match. The two files are the ground truth — no code generation; keep them in sync manually.

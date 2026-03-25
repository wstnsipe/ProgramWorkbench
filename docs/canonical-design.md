# APW Canonical Design — Source of Truth

This document supersedes all prior design outputs. When there is any conflict
between this file and prior conversation outputs, this file wins.

Last updated: 2026-03-24

---

## Contradictions resolved in this document

| # | Conflict | Decision |
|---|---------|---------|
| 1 | `interfaces` (old BriefTab, old wizard schema) vs `key_interfaces` (ORM column, new types) | **`key_interfaces` everywhere** |
| 2 | Modules saved via wizard PUT `modules` key AND via `/modules` endpoint | **`/modules` endpoint only**; wizard PUT no longer creates module rows |
| 3 | Scenarios as `g_mosa_scenarios` textarea in wizard answers AND in `mosa_scenarios` table | **`mosa_scenarios` table only**; question retired from wizard |
| 4 | Standards as `i_known_standards_architectures_mapping` textarea AND `program_standards` table | **`program_standards` table only**; question retired from wizard |
| 5 | Brief fields duplicated in wizard questions (a, b, c, d, l, m) | **Brief table is canonical** for all structured/typed fields; those questions retired |
| 6 | Sufficiency reads scenarios from `wizard_answers["g_mosa_scenarios"]` | **Sufficiency reads from `mosa_scenarios` table directly** |

---

## 1. Canonical Domain Model

### Tables and columns

```
programs
  id              integer PK
  name            text NOT NULL
  service_branch  text          -- USN | USAF | USSF | ARMY
  army_pae        text          -- ARMY only: PM_PEO_C3T | PM_PEO_IEW_S | ...
  mig_id          text          -- set by rules engine, stored for display

program_briefs
  id                    integer PK
  program_id            integer FK → programs  UNIQUE
  program_description   text
  dev_cost_estimate     float     -- $M
  production_unit_cost  float     -- $M
  timeline_months       integer
  attritable            boolean
  sustainment_tail      boolean
  software_large_part   boolean
  software_involved     boolean
  mission_critical      boolean
  safety_critical       boolean
  similar_programs_exist boolean
  updated_at            timestamptz

modules
  id                integer PK
  program_id        integer FK → programs
  name              text NOT NULL
  description       text
  rationale         text
  key_interfaces    text          -- free text: FACE, SOSA, etc.
  standards         text          -- free text: module-level standards notes
  tech_risk         boolean DEFAULT false
  obsolescence_risk boolean DEFAULT false
  cots_candidate    boolean DEFAULT false
  future_recompete  boolean DEFAULT false
  created_at        timestamptz

mosa_scenarios
  id             integer PK
  program_id     integer FK → programs
  scenario_type  text NOT NULL    -- reprocure | reuse | recompete
  module_name    text
  description    text
  word_count     integer
  updated_at     timestamptz

program_standards
  id             integer PK
  program_id     integer FK → programs
  standard_name  text NOT NULL
  applies        boolean DEFAULT false
  catalog_id     text             -- stable ID from standards catalog
  notes          text
  created_at     timestamptz

program_answers                   -- freeform text questions only (see §2)
  id           integer PK
  program_id   integer FK → programs
  question_id  text NOT NULL
  answer_text  text
  updated_at   timestamptz
  UNIQUE (program_id, question_id)

program_files
  id             integer PK
  program_id     integer FK → programs
  filename       text NOT NULL
  relative_path  text NOT NULL
  size_bytes     integer
  uploaded_at    timestamptz
  extracted_text text
  source_type    text DEFAULT 'program_input'  -- program_input | exemplar

file_chunks
  id             integer PK
  program_id     integer FK → programs
  file_id        integer FK → program_files
  source_type    text
  chunk_index    integer
  chunk_text     text
  embedding      vector(1536)
  is_heading     boolean DEFAULT false
  is_table       boolean DEFAULT false
  is_list        boolean DEFAULT false
  section_heading text
  doc_section    text
  fact_score     float
  meta_json      text
  created_at     timestamptz

rag_chunks                        -- global reference docs (MIG PDFs, etc.)
  id               integer PK
  program_id       integer          -- NULL for global reference docs
  source_filename  text
  chunk_index      integer
  chunk_text       text
  created_at       timestamptz

program_documents
  id          integer PK
  program_id  integer FK → programs
  doc_type    text     -- rfi | acq_strategy | sep | mcp
  file_path   text
  created_at  timestamptz

exemplar_styles                   -- cached per-section style excerpts
  id            integer PK
  file_id       integer FK → program_files
  doc_type      text
  section_name  text
  style_excerpt text
  extracted_at  timestamptz
  UNIQUE (file_id, doc_type, section_name)

sufficiency_logs
  id                integer PK
  program_id        integer FK → programs
  level             text     -- GREEN | YELLOW_HIGH | YELLOW_LOW | RED
  score             float
  gates_failed_json text     -- JSON array of gate_id strings
  checked_at        timestamptz
```

### Relationships

```
programs 1──* program_briefs     (UNIQUE: one brief per program)
programs 1──* modules
programs 1──* mosa_scenarios
programs 1──* program_standards
programs 1──* program_answers
programs 1──* program_files
programs 1──* program_documents
program_files 1──* file_chunks
program_files 1──* exemplar_styles
```

### What `module.standards` vs `program_standards` means

- `modules.standards` — **per-module**: free text noting which standards apply to this specific module boundary (e.g., "FACE TSS for avionics interface"). Written by the PM.
- `program_standards` — **per-program**: structured Yes/No catalog of whether a known standard (FACE, SOSA, DO-178C, etc.) applies to the program at all. Powers rules engine and document generation.

---

## 2. Canonical Wizard Schema

### Design rule

The wizard stores **only freeform text** that has no dedicated table. All structured, typed, or list data lives in dedicated tables with dedicated endpoints.

### Active questions (stored in `program_answers`)

| ID | Prompt | Type | Used in generation |
|----|--------|------|-------------------|
| `e_similar_previous_programs` | Similar previous programs or analogous systems? | textarea | context |
| `f_tech_challenges_and_risk_areas` | Key technical challenges and risk areas? | textarea | risk sections |
| `j_obsolescence_candidates` | Known/anticipated obsolescence candidates? | textarea | sustainment sections |
| `k_commercial_solutions_by_module` | Commercial solutions by module? | textarea | COTS sections |
| `n_software_standards_architectures` | Software standards and architectures? | textarea | SEP/MCP |
| `o_mosa_repo_searched` | Has the MOSA repository been searched? | select (yes/no) | MOSA sections |

### Retired questions (and where the data now lives)

| Retired ID | Replacement |
|-----------|-------------|
| `a_program_description` | `program_briefs.program_description` |
| `b_dev_cost_estimate` | `program_briefs.dev_cost_estimate` |
| `c_production_unit_cost` | `program_briefs.production_unit_cost` |
| `d_attritable_or_sustainment_tail` | `program_briefs.attritable` / `sustainment_tail` |
| `g_mosa_scenarios` | `mosa_scenarios` table |
| `h_candidate_modules` | `modules` table |
| `i_known_standards_architectures_mapping` | `program_standards` table |
| `l_software_large_part` | `program_briefs.software_large_part` |
| `m_mission_or_safety_critical` | `program_briefs.mission_critical` / `safety_critical` |

### Payload shape

```typescript
// PUT /programs/{id}/wizard
{ answers: Record<string, string> }   // only the 6 active question IDs

// GET /programs/{id}/wizard
{
  questions: QuestionOut[],           // only active questions
  answers: Record<string, string>,
  answered_count: number,
  total_count: number,                // 6
  percent_complete: number
}
```

---

## 3. Canonical Rules Catalog

### Input → Output contract

```python
# Input
RulesInput:
  service_branch:             str | None    # USN | USAF | USSF | ARMY
  army_pae:                   str | None
  dev_cost_estimate:          float | None  # $M
  production_unit_cost:       float | None  # $M
  attritable:                 bool | None
  sustainment_tail:           bool | None
  software_large_part:        bool | None
  software_involved:          bool | None
  mission_critical:           bool | None
  safety_critical:            bool | None
  similar_programs_exist:     bool | None
  timeline_months:            int | None
  module_count:               int           # default 0
  modules_with_cots:          int           # default 0
  modules_with_tech_risk:     int           # default 0
  modules_with_obsolescence_risk: int       # default 0

# Output
RulesResult:
  mig_id:                     str | None
  modifiers:                  list[DocModifier]
  violations:                 list[RuleViolation]
  recommended_module_count_min: int | None
  recommended_module_count_max: int | None
  flags:                      dict[str, bool]
```

### 12 rules

| # | ID | Trigger | Output |
|---|----|---------|--------|
| 1 | MIG_SELECT | `service_branch` is set | `mig_id` set from lookup table |
| 2 | MODULE_COUNT_BAND | `dev_cost_estimate` is set | `recommended_module_count_min/max` set; WARN if `module_count` < min |
| 3 | DO178_DO297 | `software_large_part` or `safety_critical` | `INCLUDE_DO178_DO297`, `HW_SW_SEPARATION` |
| 4 | MISSION_CRITICAL | `mission_critical` | `MISSION_CRITICAL_VERIFICATION` |
| 5 | ATTRITABLE | `attritable` | `ATTRITABLE_LIFECYCLE`; INFO violation |
| 6 | SUSTAINMENT | `sustainment_tail` | `SUSTAINMENT_TAIL_PLANNING` |
| 7 | TECH_RISK_RATIO | tech risk modules ≥ 40% of total | `HIGH_TECH_RISK_MODULAR`; flag `high_tech_risk` |
| 8 | COTS | `modules_with_cots > 0` | `EMPHASIZE_COMMERCIAL`, `COTS_REFRESH_CYCLE` |
| 9 | REUSE_TYPE | `similar_programs_exist` and `module_count == 0` | `REUSE_TYPE_ANALYSIS`; WARN violation |
| 10 | TIMELINE_SHORT | `timeline_months < 18` | WARN violation |
| 11 | NO_MODULES | `module_count == 0` | WARN violation |
| 12 | OBSOLESCENCE_HIGH | obsolescence risk modules ≥ 30% | flag `high_obsolescence_risk`; INFO violation |

### Module count bands (Rule 2)

| Dev cost | Min modules | Max modules |
|----------|-------------|-------------|
| < $50M | 3 | 5 |
| $50M – $200M | 5 | 8 |
| $200M – $500M | 7 | 12 |
| > $500M | 10 | 20 |

### DocModifier catalog

| Modifier | Injected prompt emphasis |
|----------|--------------------------|
| `INCLUDE_DO178_DO297` | Include DO-178C/DO-297 software certification requirements |
| `HW_SW_SEPARATION` | Emphasize hardware/software separation at module boundaries |
| `MISSION_CRITICAL_VERIFICATION` | Strengthen verification/validation requirements language |
| `ATTRITABLE_LIFECYCLE` | Include planned obsolescence and lifecycle cost language |
| `SUSTAINMENT_TAIL_PLANNING` | Emphasize long-term sustainment, logistics, DMSMS planning |
| `HIGH_TECH_RISK_MODULAR` | Emphasize modular decomposition to manage tech risk |
| `EMPHASIZE_COMMERCIAL` | Lead with commercial-first, COTS/MOTS preference language |
| `COTS_REFRESH_CYCLE` | Include COTS technology refresh cycle planning |
| `REUSE_TYPE_ANALYSIS` | Include reuse type analysis (adopt/adapt/extend) |

### Sufficiency gates (4 — any failure → RED)

| Gate ID | Condition |
|---------|-----------|
| `PROGRAM_NAME` | `programs.name` is non-empty |
| `DESCRIPTION` | `program_briefs.program_description` is non-empty |
| `SERVICE_BRANCH` | `programs.service_branch` is non-null |
| `MODULES_EXIST` | at least 1 row in `modules` for this program |

### Coverage weights (sum = 100)

| Field | Source table | Weight |
|-------|-------------|--------|
| Program description | `program_briefs` | 15 |
| Service branch | `programs` | 8 |
| Dev cost estimate | `program_briefs` | 7 |
| Timeline months | `program_briefs` | 6 |
| Production unit cost | `program_briefs` | 5 |
| Modules defined | `modules` | 20 |
| MOSA scenarios (≥ 2) | `mosa_scenarios` | 12 |
| Standards identified (≥ 1) | `program_standards` | 7 |
| Attritable flag set | `program_briefs` | 4 |
| Mission critical set | `program_briefs` | 4 |
| Safety critical set | `program_briefs` | 4 |
| Software large part set | `program_briefs` | 3 |
| Files uploaded (≥ 1) | `program_files` | 5 |

### Sufficiency levels

| Level | Condition | Blocks generation? |
|-------|-----------|-------------------|
| `RED` | Any gate failed | Yes |
| `YELLOW_LOW` | No gates failed; score < 55 | No (placeholders inserted) |
| `YELLOW_HIGH` | No gates failed; 55 ≤ score < 80 | No |
| `GREEN` | No gates failed; score ≥ 80 | No |

---

## 4. Canonical Document Generation Architecture

### Pipeline (per document)

```
1. Load data
   └─ program, brief, modules, wizard_answers (6 keys), scenarios, standards

2. Run rules engine
   └─ RulesInput ──→ RulesResult { mig_id, modifiers, violations }
   └─ mig_id written back to programs.mig_id

3. Build full fact pack (flat dict)
   └─ { program_name, service_branch, mig_id,
        program_description, dev_cost_estimate, production_unit_cost,
        timeline_months, attritable, sustainment_tail, software_large_part,
        mission_critical, safety_critical, similar_programs_exist,
        modules[], scenarios[], standards[], wizard_answers{},
        cots_count, modifiers[] }

4. For each section in TEMPLATE_REGISTRY[doc_type].section_order:
   a. Slice fact pack → only keys in SectionDef.fact_keys
   b. Hybrid search → top-8 chunks (program_files + rag_chunks)
   c. Fetch exemplar style excerpt ≤ 600 chars (from exemplar_styles)
   d. Call section_generator.generate_section()
      └─ system prompt ≤ 25 lines
      └─ user message: facts (JSON) + chunks + schema + instruction
      └─ response_format: json_object
      └─ validate against section's Pydantic schema
      └─ retry once on failure
   e. Accumulate section output dict

5. Render to DOCX
   └─ renderer.py → docx_builder.py build_{doc_type}_docx()

6. Persist ProgramDocument row, return download path
```

### Section definitions per doc type

**rfi** (4 sections)

| Section | Schema | Key fact_keys |
|---------|--------|--------------|
| Overview & Purpose | `RfiOverviewSection` | program_name, program_description, service_branch, dev_cost_estimate |
| MOSA Requirements | `RfiMosaSection` | modules, mig_id, modifiers, standards |
| Questions to Industry | `RfiQuestionsSection` | program_description, modules, standards, scenarios |
| Deliverables & Submission | `RfiDeliverablesSection` | service_branch, timeline_months |

**acq_strategy** (6 sections)

| Section | Schema | Key fact_keys |
|---------|--------|--------------|
| Executive Summary | `AcqExecSummarySection` | program_name, program_description, service_branch, dev_cost_estimate, timeline_months |
| Schedule & Milestones | `AcqScheduleSection` | timeline_months, program_description, attritable |
| Cost Estimates | `AcqCostSection` | dev_cost_estimate, production_unit_cost |
| Risk Register | `AcqRiskSection` | modules, modifiers, mission_critical, safety_critical |
| MOSA & Data Rights | `AcqMosaSection` | modules, mig_id, standards, modifiers, scenarios |
| Contracting Strategy | `AcqContractingSection` | dev_cost_estimate, attritable, cots_count, service_branch |

**sep** (4 sections)

| Section | Schema | Key fact_keys |
|---------|--------|--------------|
| Technical Reviews & Requirements | `SepTechSection` | timeline_months, mission_critical, safety_critical |
| Architecture & MOSA | `SepArchSection` | modules, standards, mig_id, modifiers |
| Risk Management | `SepRiskSection` | modules, modifiers, safety_critical |
| Verification & Validation | `SepVnVSection` | modifiers, safety_critical, mission_critical, software_large_part |

**mcp** (3 sections)

| Section | Schema | Key fact_keys |
|---------|--------|--------------|
| Conformance Overview | `McpOverviewSection` | program_name, program_description, mig_id, modules |
| Module Assessments | `McpModuleSection` | modules, standards, modifiers |
| Verification Milestones | `McpVerificationSection` | timeline_months, mission_critical, modules |

### LLM call parameters

```python
model:           OPENAI_MODEL env var (default gpt-4o-mini)
temperature:     0.3
max_tokens:      2048
response_format: {"type": "json_object"}
retries:         1 (total 2 attempts)
```

### Estimated token budget per document

| Doc type | Sections | ~tokens/section | ~total |
|----------|----------|-----------------|--------|
| rfi | 4 | 800 | 3,200 |
| acq_strategy | 6 | 1,000 | 6,000 |
| sep | 4 | 900 | 3,600 |
| mcp | 3 | 900 | 2,700 |

---

## 5. Canonical API — Endpoints and Payloads

### Programs

```
POST   /programs                    → Program
GET    /programs                    → Program[]
GET    /programs/{id}               → Program
PATCH  /programs/{id}               → Program

Program { id, name, service_branch, army_pae, mig_id }
```

### Brief

```
GET    /programs/{id}/brief         → ProgramBrief | 404
PUT    /programs/{id}/brief         → ProgramBrief

ProgramBrief {
  program_id, program_description, dev_cost_estimate, production_unit_cost,
  timeline_months, attritable, sustainment_tail, software_large_part,
  software_involved, mission_critical, safety_critical, similar_programs_exist,
  updated_at
}
```

### Wizard (freeform text only)

```
GET    /programs/{id}/wizard        → WizardState
PUT    /programs/{id}/wizard        → 204

PUT body: { answers: Record<string, string> }
Valid keys: e_similar_previous_programs, f_tech_challenges_and_risk_areas,
            j_obsolescence_candidates, k_commercial_solutions_by_module,
            n_software_standards_architectures, o_mosa_repo_searched
```

### Modules (bulk replace)

```
GET    /programs/{id}/modules       → Module[]
PUT    /programs/{id}/modules       → Module[]   (replaces all; skips empty name rows)
DELETE /programs/{id}/modules/{mid} → 204

Module { id, program_id, name, description, rationale, key_interfaces, standards,
         tech_risk, obsolescence_risk, cots_candidate, future_recompete, created_at }

PUT body: { modules: ModuleRow[] }
ModuleRow { name, description, rationale, key_interfaces, standards,
            tech_risk, obsolescence_risk, cots_candidate, future_recompete }
```

### Scenarios (bulk replace)

```
GET    /programs/{id}/scenarios     → MosaScenario[]
PUT    /programs/{id}/scenarios     → MosaScenario[]

MosaScenario { id, program_id, scenario_type, module_name, description,
               word_count, updated_at }
scenario_type: "reprocure" | "reuse" | "recompete"

PUT body: { scenarios: ScenarioRow[] }
ScenarioRow { scenario_type, module_name, description }
```

### Standards (bulk replace)

```
GET    /programs/{id}/standards     → ProgramStandard[]
PUT    /programs/{id}/standards     → ProgramStandard[]

ProgramStandard { id, program_id, standard_name, applies, catalog_id,
                  notes, created_at }

PUT body: { standards: StandardRow[] }
StandardRow { standard_name, applies, catalog_id, notes }
```

### Sufficiency

```
GET    /programs/{id}/sufficiency   → SufficiencyResult

SufficiencyResult {
  level: "GREEN" | "YELLOW_HIGH" | "YELLOW_LOW" | "RED",
  score: float,
  gates: GateResult[],
  coverage: FieldCoverage[],
  missing_critical: string[],
  warnings: string[],
  mig_id: string | null,
  modifiers: string[],
  rule_violations: RuleViolation[]
}
```

### Files

```
POST   /programs/{id}/files                    → ProgramFile[]   (multipart)
GET    /programs/{id}/files                    → ProgramFile[]
POST   /programs/{id}/files/{fid}/extract      → ExtractionResult
DELETE /programs/{id}/files/{fid}              → 204

POST body: FormData { files: File[], source_type: "program_input" | "exemplar" }
```

### Documents

```
GET    /programs/{id}/documents                → ProgramDocument[]
POST   /programs/{id}/documents/generate       → GenerateDocResult   (202 queued)
GET    /programs/{id}/documents/{did}/download → .docx stream

POST body: { doc_type: "rfi" | "acq_strategy" | "sep" | "mcp", force?: bool }

GenerateDocResult { job_id, status, doc_type, program_id, document_id,
                    download_url, error }
```

---

## 6. Canonical Frontend → Backend Payload Alignment

### `ModuleRow` field names — canonical

```typescript
// frontend: src/types/index.ts
interface ModuleRow {
  name:              string    // required; blank rows are skipped on save
  description:       string
  rationale:         string
  key_interfaces:    string    // ← was "interfaces" in old BriefTab — FIXED
  standards:         string    // per-module standards notes (free text)
  tech_risk:         boolean
  obsolescence_risk: boolean
  cots_candidate:    boolean
  future_recompete:  boolean
}
```

```python
# backend: schemas_v2.py
class ModuleInV2(BaseModel):
    name:              str
    description:       Optional[str] = None
    rationale:         Optional[str] = None
    key_interfaces:    Optional[str] = None   # ← matches frontend exactly
    standards:         Optional[str] = None
    tech_risk:         bool = False
    obsolescence_risk: bool = False
    cots_candidate:    bool = False
    future_recompete:  bool = False
```

### `BriefFormState` → `PUT /programs/{id}/brief` mapping

```typescript
// Frontend form state (strings for number inputs)
interface BriefFormState {
  program_description:   string
  dev_cost_estimate:     string   // parsed to float | null on save
  production_unit_cost:  string   // parsed to float | null on save
  timeline_months:       string   // parsed to int | null on save
  attritable:            boolean
  sustainment_tail:      boolean
  software_large_part:   boolean
  software_involved:     boolean
  mission_critical:      boolean
  safety_critical:       boolean
  similar_programs_exist: boolean
}
```

---

## 7. Canonical Implementation Order

Work in this order. Each sprint is independently shippable.

### Sprint 1 — Data model stabilization (foundation)
1. Run `MIGRATION_SQL` from `models_v2.py` to add new columns
2. Create `mosa_scenarios`, `program_standards`, `exemplar_styles`, `sufficiency_logs` tables
3. Update `backend/config/questions.yaml` — remove 9 retired questions, keep 6
4. Update `PUT /programs/{id}/wizard` — remove `modules` key handling (no longer creates Module rows)
5. Fix `BriefTab.tsx` `ModuleItem.interfaces` → `key_interfaces` (one rename)
6. Fix `sufficiency_service.py` — read scenarios count from `mosa_scenarios` table, not `wizard_answers`

**Acceptance**: schema is clean; old endpoints still work; no 500 errors.

### Sprint 2 — New dedicated endpoints (backend)
1. Wire `routers/modules.py` into `main.py` (or use `main_v2.py`)
2. Wire `routers/scenarios.py`
3. Wire `routers/standards.py`
4. Wire `routers/sufficiency.py`
5. Wire `routers/programs.py` for PATCH (service_branch)
6. Smoke test all 5 new routers via `/docs`

**Acceptance**: all 5 new routers return correct data; existing UI still works.

### Sprint 3 — Brief tab rebuild (frontend)
1. Add `ServiceBranchField` to BriefTab (uses PATCH `/programs/{id}`)
2. Add `timeline_months`, `software_involved`, `similar_programs_exist` to brief form
3. Replace `ModulesBuilder` with `ModuleListEditor` + `useModules` hook
4. Replace `g_mosa_scenarios` textarea with `ScenarioCards` + `useScenarios` hook
5. Replace `i_known_standards_architectures_mapping` textarea with `StandardsEditor` + `useStandards` hook
6. Add `SufficiencyBanner` at top of BriefTab (lazy refresh after save)
7. Replace manual save row with `SaveBar`

**Acceptance**: full Brief tab works end-to-end with new endpoints; old wizard questions removed from UI.

### Sprint 4 — Rules engine + sufficiency (wired end-to-end)
1. Verify `evaluate_rules()` is called from both sufficiency endpoint and generation orchestrator
2. Wire `mig_id` from `RulesResult` back to `programs.mig_id` on generation
3. Display MIG ID in `SufficiencyBanner` and program header
4. Show rule violations in sufficiency detail view

**Acceptance**: change service_branch → sufficiency refreshes → MIG appears; violations shown.

### Sprint 5 — Section-by-section generation
1. Register all 4 doc types in `generation/orchestrator.py` `SECTION_MAP`
2. Hook orchestrator into `routers/documents.py` background task
3. Verify existing `docx_builder.py` functions are called via `renderer.py` fallback
4. Add generation status polling (poll `GET /programs/{id}/documents` until new doc appears)
5. Test each of 4 doc types end-to-end

**Acceptance**: all 4 doc types generate and download without errors.

### Sprint 6 — RAG improvements
1. Add structure-aware chunking to `llm/retrieval.py` (heading/table/list detection)
2. Add the 6 new metadata columns to `file_chunks`
3. Replace keyword RAG with hybrid search (pgvector cosine + PostgreSQL FTS, RRF fusion)
4. Test retrieval quality on a real program with uploaded files

**Acceptance**: retrieved chunks are more relevant; generated documents cite source files.

### Sprint 7 — Exemplar style extraction
1. Implement `POST /programs/{id}/files/{fid}/extract-exemplar-styles`
2. Populate `exemplar_styles` table per section per exemplar file
3. Wire style excerpts into `orchestrator._get_exemplar_style()`
4. Test: upload exemplar → generation uses its style

**Acceptance**: documents with an exemplar uploaded match exemplar tone/structure more closely.

---

## 8. Key Decisions and Tradeoffs

| Decision | Rationale | Tradeoff |
|----------|-----------|---------|
| Bulk replace for modules/scenarios/standards (PUT replaces all) | Simpler than per-row PATCH; UI always has the full list | Concurrent edits from two sessions will clobber each other — acceptable for single-user program offices |
| Wizard answers table only for freeform text (6 questions) | Avoids dual-write bugs; structured data has correct types in dedicated tables | Breaks backward compat with existing `program_answers` rows for retired keys — accept and ignore them |
| Rules engine produces `DocModifier` strings, not prompt text | Keeps prompts in one place; modifiers are declarative intent | Developer must remember to update prompt instructions when adding a modifier |
| Section-by-section generation vs one monolithic call | Better output quality per section; targeted facts; cheaper total tokens | More HTTP calls to OpenAI; total latency is higher — mitigated by background task |
| `response_format: json_object` + Pydantic validation | Eliminates markdown contamination; retry on schema failure | Requires strict schema adherence; complex nested schemas increase retry rate — keep schemas flat |
| gpt-4o-mini as default model | ~10× cheaper than gpt-4o for most sections | Lower output quality on complex sections (risk register, MOSA analysis) — switch specific sections to gpt-4o via `OPENAI_MODEL` override if needed |
| `mig_id` stored in `programs` table | Fast access for display; avoids re-running rules on every GET | Can drift from rules output if program data changes without re-running sufficiency — acceptable |
| Sufficiency reads from dedicated tables (not wizard_answers) | Accurate counts; no JSON parsing of textarea strings | Requires that modules/scenarios/standards be saved via their dedicated endpoints before checking |
| `program_files.source_type = "exemplar"` | No separate exemplar file table; reuses existing upload/extraction pipeline | Cannot distinguish exemplar-specific metadata without filtering; manageable |
| No Alembic — use raw SQL migrations | Simpler for a small team; no migration history to manage | No automatic rollback; migrations must be idempotent (`IF NOT EXISTS`) |

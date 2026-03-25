// ─────────────────────────────────────────────────────────────────────────────
// Core domain types — mirror backend/contracts.py
// Keep these two files in sync. No code generation; manual sync is intentional.
// ─────────────────────────────────────────────────────────────────────────────

export type ServiceBranch = 'USN' | 'USAF' | 'USSF' | 'ARMY'
export type DocType = 'rfi' | 'acq_strategy' | 'sep' | 'mcp'
export type ScenarioType = 'reprocure' | 'reuse' | 'recompete'
export type SufficiencyLevel = 'GREEN' | 'YELLOW_HIGH' | 'YELLOW_LOW' | 'RED'

// ── Program ───────────────────────────────────────────────────────────────────

export interface Program {
  id: number
  name: string
  service_branch: ServiceBranch | null
  army_pae: string | null
  mig_id: string | null
}

export interface ProgramCreatePayload {
  name: string
  service_branch?: ServiceBranch
  army_pae?: string
}

// ── Program Brief ─────────────────────────────────────────────────────────────

export interface ProgramBrief {
  program_id: number
  program_description: string | null
  dev_cost_estimate: number | null
  production_unit_cost: number | null
  timeline_months: number | null
  attritable: boolean | null
  sustainment_tail: boolean | null
  software_large_part: boolean | null
  software_involved: boolean | null
  mission_critical: boolean | null
  safety_critical: boolean | null
  similar_programs_exist: boolean | null
  updated_at: string
}

/** Form state uses strings for numeric inputs (avoids controlled/uncontrolled issues) */
export interface BriefFormState {
  program_description: string
  dev_cost_estimate: string
  production_unit_cost: string
  timeline_months: string
  attritable: boolean
  sustainment_tail: boolean
  software_large_part: boolean
  software_involved: boolean
  mission_critical: boolean
  safety_critical: boolean
  similar_programs_exist: boolean
}

// ── Module ────────────────────────────────────────────────────────────────────

export interface Module {
  id: number
  program_id: number
  name: string
  description: string | null
  rationale: string | null
  key_interfaces: string | null
  standards: string | null
  tech_risk: boolean
  obsolescence_risk: boolean
  cots_candidate: boolean
  future_recompete: boolean
  created_at: string
}

/** Editable row — no id/program_id/created_at */
export interface ModuleRow {
  name: string
  description: string
  rationale: string
  key_interfaces: string
  standards: string
  tech_risk: boolean
  obsolescence_risk: boolean
  cots_candidate: boolean
  future_recompete: boolean
}

export const EMPTY_MODULE_ROW: ModuleRow = {
  name: '',
  description: '',
  rationale: '',
  key_interfaces: '',
  standards: '',
  tech_risk: false,
  obsolescence_risk: false,
  cots_candidate: false,
  future_recompete: false,
}

// ── MOSA Scenarios ────────────────────────────────────────────────────────────

export interface MosaScenario {
  id: number
  program_id: number
  scenario_type: ScenarioType
  module_name: string | null
  description: string | null
  word_count: number | null
  created_at: string
  updated_at: string
}

export interface ScenarioRow {
  scenario_type: ScenarioType
  module_name: string
  description: string
}

export const SCENARIO_LABELS: Record<ScenarioType, string> = {
  reprocure: 'Reprocure',
  reuse:     'Reuse',
  recompete: 'Recompete',
}

export const SCENARIO_DESCRIPTIONS: Record<ScenarioType, string> = {
  reprocure: 'Government reprocures the module from a new or different vendor using open interface specs',
  reuse:     'Module is adopted or adapted from an existing system or program',
  recompete: 'Module contract is recompeted at end of period of performance using modular boundaries',
}

// ── Standards ─────────────────────────────────────────────────────────────────

export interface ProgramStandard {
  id: number
  program_id: number
  standard_name: string
  applies: boolean
  catalog_id: string | null
  notes: string | null
  created_at: string
}

export interface StandardRow {
  standard_name: string
  applies: boolean
  catalog_id: string | null
  notes: string
}

/** Catalog of known standards for the dropdown */
export interface StandardCatalogEntry {
  catalog_id: string
  name: string
  description: string
  branches: ServiceBranch[]  // empty = all branches
}

// ── Sufficiency ───────────────────────────────────────────────────────────────

export interface GateResult {
  gate_id: string
  passed: boolean
  message: string
}

export interface FieldCoverage {
  field_id: string
  label: string
  weight: number
  present: boolean
  source: string
}

export interface RuleViolation {
  rule_id: string
  severity: 'ERROR' | 'WARN' | 'INFO'
  message: string
}

export interface SufficiencyResult {
  level: SufficiencyLevel
  score: number
  gates: GateResult[]
  coverage: FieldCoverage[]
  missing_critical: string[]
  warnings: string[]
  mig_id: string | null
  modifiers: string[]
  rule_violations: RuleViolation[]
}

// ── Files ─────────────────────────────────────────────────────────────────────

export type FileSourceType = 'program_input' | 'exemplar'

export interface ProgramFile {
  id: number
  program_id: number
  filename: string
  relative_path: string
  size_bytes: number
  uploaded_at: string
  extracted_text: string | null
  source_type: FileSourceType
}

export interface ExtractionResult {
  file_id: number
  filename: string
  chars_extracted: number
  chunks_created: number
  error: string | null
}

// ── Documents ─────────────────────────────────────────────────────────────────

export interface ProgramDocument {
  id: number
  program_id: number
  doc_type: DocType
  file_path: string
  created_at: string
}

export type GenerationStatus = 'queued' | 'generating' | 'done' | 'error'

export interface GenerateDocResult {
  job_id: string
  status: GenerationStatus
  doc_type: DocType
  program_id: number
  document_id: number | null
  download_url: string | null
  error: string | null
}

// ── Wizard ────────────────────────────────────────────────────────────────────

export interface WizardQuestion {
  id: string
  prompt: string
  help: string
  type: string
  options: Array<{ value: string; label: string }> | null
  missing: boolean
}

export interface WizardState {
  questions: WizardQuestion[]
  answers: Record<string, unknown>
  answered_count: number
  total_count: number
  percent_complete: number
}

// ── API errors ────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string | Record<string, unknown>
  status: number
}

// ── UI state helpers ──────────────────────────────────────────────────────────

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error'
export type LoadStatus = 'idle' | 'loading' | 'loaded' | 'error'

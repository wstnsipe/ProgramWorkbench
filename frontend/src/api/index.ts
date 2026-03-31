/**
 * api/index.ts — single import point for all API functions.
 *
 * Usage:
 *   import * as api from '../api'
 *   const program = await api.getProgram(id)
 */

import { apiGet, apiPost, apiPut, apiPatch, apiDelete, apiUpload, apiDownloadUrl } from './client'
import type {
  Program, ProgramCreatePayload,
  ProgramBrief, BriefFormState,
  Module, ModuleRow,
  MosaScenario, ScenarioRow,
  ProgramStandard, StandardRow,
  SufficiencyResult,
  ProgramFile, ExtractionResult,
  ProgramDocument, GenerateDocResult,
  WizardState, DocType,
} from '../types'

// ── Programs ──────────────────────────────────────────────────────────────────

export const listPrograms = (): Promise<Program[]> =>
  apiGet('/programs')

export const getProgram = (id: number | string): Promise<Program> =>
  apiGet(`/programs/${id}`)

export const createProgram = (payload: ProgramCreatePayload): Promise<Program> =>
  apiPost('/programs', payload)

export const updateProgram = (
  id: number | string,
  payload: Partial<Pick<Program, 'name' | 'service_branch' | 'army_pae'>>,
): Promise<Program> =>
  apiPatch(`/programs/${id}`, payload)

export const deleteProgram = (id: number | string): Promise<void> =>
  apiDelete(`/programs/${id}`)

// ── Brief ─────────────────────────────────────────────────────────────────────

export const getBrief = (programId: number | string): Promise<ProgramBrief | null> =>
  apiGet<ProgramBrief>(`/programs/${programId}/brief`).catch(() => null)

export const saveBrief = (
  programId: number | string,
  form: BriefFormState,
): Promise<ProgramBrief> => {
  const payload = {
    program_description: form.program_description || null,
    dev_cost_estimate:   form.dev_cost_estimate   !== '' ? parseFloat(form.dev_cost_estimate)   : null,
    production_unit_cost: form.production_unit_cost !== '' ? parseFloat(form.production_unit_cost) : null,
    timeline_months:     form.timeline_months     !== '' ? parseInt(form.timeline_months, 10)    : null,
    attritable:           form.attritable,
    sustainment_tail:     form.sustainment_tail,
    software_large_part:  form.software_large_part,
    software_involved:    form.software_involved,
    mission_critical:     form.mission_critical,
    safety_critical:      form.safety_critical,
    similar_programs_exist: form.similar_programs_exist,
  }
  return apiPut(`/programs/${programId}/brief`, payload)
}

// ── Wizard ────────────────────────────────────────────────────────────────────

export const getWizard = (programId: number | string): Promise<WizardState> =>
  apiGet(`/programs/${programId}/wizard`)

export const saveWizardAnswers = (
  programId: number | string,
  answers: Record<string, unknown>,
): Promise<void> =>
  apiPut(`/programs/${programId}/wizard`, { answers })

// ── Modules ───────────────────────────────────────────────────────────────────

export const listModules = (programId: number | string): Promise<Module[]> =>
  apiGet(`/programs/${programId}/modules`)

export const replaceModules = (
  programId: number | string,
  modules: ModuleRow[],
): Promise<Module[]> =>
  apiPut(`/programs/${programId}/modules`, { modules })

export const deleteModule = (programId: number | string, moduleId: number): Promise<void> =>
  apiDelete(`/programs/${programId}/modules/${moduleId}`)

export const listMismatches = (programId: number | string): Promise<import('../types').RuleViolation[]> =>
  apiGet(`/programs/${programId}/modules/mismatches`)

// ── Scenarios ─────────────────────────────────────────────────────────────────

export const listScenarios = (programId: number | string): Promise<MosaScenario[]> =>
  apiGet(`/programs/${programId}/scenarios`)

export const replaceScenarios = (
  programId: number | string,
  scenarios: ScenarioRow[],
): Promise<MosaScenario[]> =>
  apiPut(`/programs/${programId}/scenarios`, { scenarios })

// ── Standards ─────────────────────────────────────────────────────────────────

export const listStandards = (programId: number | string): Promise<ProgramStandard[]> =>
  apiGet(`/programs/${programId}/standards`)

export const replaceStandards = (
  programId: number | string,
  standards: StandardRow[],
): Promise<ProgramStandard[]> =>
  apiPut(`/programs/${programId}/standards`, { standards })

// ── Sufficiency ───────────────────────────────────────────────────────────────

export const getSufficiency = (programId: number | string): Promise<SufficiencyResult> =>
  apiGet(`/programs/${programId}/sufficiency`)

// ── Files ─────────────────────────────────────────────────────────────────────

export const listFiles = (programId: number | string, sourceType?: string): Promise<ProgramFile[]> => {
  const qs = sourceType ? `?source_type=${sourceType}` : ''
  return apiGet(`/programs/${programId}/files${qs}`)
}

export const uploadFiles = (
  programId: number | string,
  files: File[],
  sourceType: 'program_input' | 'exemplar' = 'program_input',
): Promise<ProgramFile[]> => {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  form.append('source_type', sourceType)
  return apiUpload(`/programs/${programId}/files`, form)
}

export const extractFile = (
  programId: number | string,
  fileId: number,
): Promise<ExtractionResult> =>
  apiPost(`/programs/${programId}/files/${fileId}/extract`)

export const deleteFile = (programId: number | string, fileId: number): Promise<void> =>
  apiDelete(`/programs/${programId}/files/${fileId}`)

// ── Documents ─────────────────────────────────────────────────────────────────

export const listDocuments = (programId: number | string): Promise<ProgramDocument[]> =>
  apiGet(`/programs/${programId}/documents`)

export const generateDocument = (
  programId: number | string,
  docType: DocType,
  force = false,
): Promise<GenerateDocResult> =>
  apiPost(`/programs/${programId}/documents/generate`, { doc_type: docType, force })

export const getDocumentDownloadUrl = (
  programId: number | string,
  documentId: number,
): string =>
  apiDownloadUrl(`/programs/${programId}/documents/${documentId}/download`)

import type { ModuleRow, ScenarioRow } from '../types'

function norm(text: string): string {
  return text.toLowerCase().replace(/\s+/g, ' ').trim()
}

/** Extract module name from "For the X module, the USG desires..." format */
function extractModuleFromDescription(desc: string): string {
  const m = desc.match(/For the (.+?) module/i)
  return m ? m[1].trim() : ''
}

/**
 * Returns human-readable warning strings for module ↔ scenario mismatches.
 * Pure function — no API call needed. Used for live/instant feedback.
 *
 * Rule 1: A module name is not mentioned in any scenario description.
 * Rule 2: A scenario description references a module name not in the module list.
 */
export function moduleScenarioWarnings(
  modules: ModuleRow[],
  scenarios: ScenarioRow[],
): string[] {
  const warnings: string[] = []

  const moduleNames = modules.map(m => m.name).filter(n => n.trim())
  const filledScenarios = scenarios.filter(s => (s.description ?? '').trim())

  if (!moduleNames.length || !filledScenarios.length) return warnings

  const scenarioBlob = filledScenarios
    .map(s => s.description ?? '')
    .join(' ')
    .toLowerCase()

  const knownNorms = moduleNames.map(norm)

  // Rule 1: module name not found anywhere in scenario text
  for (const name of moduleNames) {
    if (!scenarioBlob.includes(norm(name))) {
      warnings.push(`"${name}" module has no matching scenario`)
    }
  }

  // Rule 2: module name extracted from "For the X module..." not in module list
  const seen = new Set<string>()
  for (const s of filledScenarios) {
    const extracted = extractModuleFromDescription(s.description ?? '')
    if (!extracted) continue
    const normExtracted = norm(extracted)
    if (seen.has(normExtracted)) continue
    const matched = knownNorms.some(k => normExtracted.includes(k) || k.includes(normExtracted))
    if (!matched) {
      seen.add(normExtracted)
      warnings.push(`Scenario references "${extracted}" which is not in the module list`)
    }
  }

  return warnings
}

import type { ModuleRow, ScenarioRow } from '../types'

function norm(text: string): string {
  return text.toLowerCase().replace(/\s+/g, ' ').trim()
}

/**
 * Returns human-readable warning strings for module ↔ scenario mismatches.
 * Pure function — no API call needed.
 *
 * Rule 1: A filled module name is not mentioned in any scenario.
 * Rule 2: A scenario's module_name doesn't fuzzy-match any known module.
 */
export function moduleScenarioWarnings(
  modules: ModuleRow[],
  scenarios: ScenarioRow[],
): string[] {
  const warnings: string[] = []

  const moduleNames = modules.map(m => m.name).filter(n => n.trim())
  const filledScenarios = scenarios.filter(s => s.description.trim())

  if (!moduleNames.length || !filledScenarios.length) return warnings

  const scenarioBlob = filledScenarios
    .map(s => `${s.description} ${s.module_name}`)
    .join(' ')
    .toLowerCase()

  const knownNorms = moduleNames.map(norm)

  // Rule 1: module not in any scenario
  for (const name of moduleNames) {
    if (!scenarioBlob.includes(norm(name))) {
      warnings.push(`"${name}" module has no matching scenario`)
    }
  }

  // Rule 2: scenario module_name not in module list (deduplicated)
  const seen = new Set<string>()
  for (const s of filledScenarios) {
    const sname = s.module_name.trim()
    if (!sname) continue
    const normSname = norm(sname)
    if (seen.has(normSname)) continue
    const matched = knownNorms.some(k => normSname.includes(k) || k.includes(normSname))
    if (!matched) {
      seen.add(normSname)
      warnings.push(`Scenario references "${sname}" which is not in the module list`)
    }
  }

  return warnings
}

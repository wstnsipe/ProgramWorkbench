import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { ScenarioRow, ScenarioType, SaveStatus } from '../types'

const DEFAULT_SCENARIOS: ScenarioRow[] = [
  { scenario_type: 'reprocure', module_name: '', description: '' },
  { scenario_type: 'reuse',     module_name: '', description: '' },
  { scenario_type: 'recompete', module_name: '', description: '' },
]

/** Auto-extract module name from "For the X module..." prefix */
function extractModuleName(text: string): string {
  const match = text.match(/^[Ff]or the ([^,.]+) module/i)
  return match ? match[1].trim() : ''
}

export function useScenarios(programId: string | number) {
  const [scenarios, setScenarios] = useState<ScenarioRow[]>(DEFAULT_SCENARIOS)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  useEffect(() => {
    let cancelled = false
    api.listScenarios(programId).then(data => {
      if (cancelled) return
      if (data.length > 0) {
        setScenarios(data.map(s => ({
          scenario_type: s.scenario_type,
          module_name:   s.module_name ?? '',
          description:   s.description ?? '',
        })))
      }
    }).catch(() => {})
    return () => { cancelled = true }
  }, [programId])

  const updateScenario = useCallback((
    type: ScenarioType,
    field: keyof ScenarioRow,
    value: string,
  ) => {
    setScenarios(prev => prev.map(s =>
      s.scenario_type === type ? { ...s, [field]: value } : s
    ))

    // Auto-extract module name when description is typed
    if (field === 'description') {
      const extracted = extractModuleName(value)
      if (extracted) {
        setScenarios(prev => prev.map(s =>
          s.scenario_type === type && !s.module_name
            ? { ...s, module_name: extracted }
            : s
        ))
      }
    }
  }, [])

  const save = useCallback(async (): Promise<boolean> => {
    setSaveStatus('saving')
    try {
      const filled = scenarios.filter(s => s.description.trim())
      await api.replaceScenarios(programId, filled)
      setSaveStatus('saved')
      return true
    } catch {
      setSaveStatus('error')
      return false
    }
  }, [scenarios, programId])

  const wordCounts = scenarios.reduce<Record<ScenarioType, number>>(
    (acc, s) => ({ ...acc, [s.scenario_type]: s.description.split(/\s+/).filter(Boolean).length }),
    { reprocure: 0, reuse: 0, recompete: 0 },
  )

  return { scenarios, updateScenario, save, saveStatus, wordCounts }
}

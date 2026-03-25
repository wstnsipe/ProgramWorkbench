import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { ScenarioRow, ScenarioType, SaveStatus } from '../types'
import { EMPTY_SCENARIO_ROW } from '../types'

const MIN_ROWS = 3

const DEFAULT_SCENARIOS: ScenarioRow[] = [
  { scenario_type: 'reprocure', module_name: '', description: '' },
  { scenario_type: 'reuse',     module_name: '', description: '' },
  { scenario_type: 'recompete', module_name: '', description: '' },
]

function padRows(rows: ScenarioRow[]): ScenarioRow[] {
  const result = [...rows]
  const types: ScenarioRow['scenario_type'][] = ['reprocure', 'reuse', 'recompete']
  while (result.length < MIN_ROWS) {
    result.push({ ...EMPTY_SCENARIO_ROW, scenario_type: types[result.length] ?? 'reprocure' })
  }
  return result
}

/** Auto-extract module name from "For the X module..." prefix */
function extractModuleName(text: string): string {
  const match = text.match(/^[Ff]or (?:the )?([^,.]+?) module/i)
  return match ? match[1].trim() : ''
}

export function useScenarios(programId: string | number) {
  const [scenarios, setScenarios] = useState<ScenarioRow[]>(DEFAULT_SCENARIOS)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  useEffect(() => {
    let cancelled = false
    api.listScenarios(programId).then(data => {
      if (cancelled) return
      const converted: ScenarioRow[] = data.map(s => ({
        scenario_type: s.scenario_type,
        module_name:   s.module_name ?? '',
        description:   s.description ?? '',
      }))
      setScenarios(padRows(converted))
    }).catch(() => {})
    return () => { cancelled = true }
  }, [programId])

  const updateScenario = useCallback((index: number, field: keyof ScenarioRow, value: string) => {
    setScenarios(prev => {
      const next = [...prev]
      const updated = { ...next[index], [field]: value }
      if (field === 'description') {
        const extracted = extractModuleName(value)
        if (extracted && !next[index].module_name) {
          updated.module_name = extracted
        }
      }
      next[index] = updated
      return next
    })
  }, [])

  const addScenario = useCallback(() => {
    setScenarios(prev => [...prev, { ...EMPTY_SCENARIO_ROW }])
  }, [])

  const removeScenario = useCallback((index: number) => {
    setScenarios(prev => {
      const next = prev.filter((_, i) => i !== index)
      return padRows(next)
    })
  }, [])

  const save = useCallback(async (): Promise<boolean> => {
    setSaveStatus('saving')
    try {
      const filled = scenarios.filter(s => s.description.trim())
      const saved = await api.replaceScenarios(programId, filled)
      const converted: ScenarioRow[] = saved.map(s => ({
        scenario_type: s.scenario_type,
        module_name:   s.module_name ?? '',
        description:   s.description ?? '',
      }))
      setScenarios(padRows(converted))
      setSaveStatus('saved')
      return true
    } catch {
      setSaveStatus('error')
      return false
    }
  }, [scenarios, programId])

  const wordCounts = scenarios.map(s =>
    s.description.split(/\s+/).filter(Boolean).length
  )

  return { scenarios, updateScenario, addScenario, removeScenario, save, saveStatus, wordCounts }
}

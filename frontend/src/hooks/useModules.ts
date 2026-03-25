import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { ModuleRow, SaveStatus } from '../types'
import { EMPTY_MODULE_ROW } from '../types'

const MIN_ROWS = 5

function padRows(rows: ModuleRow[]): ModuleRow[] {
  const result = [...rows]
  while (result.length < MIN_ROWS) result.push({ ...EMPTY_MODULE_ROW })
  return result
}

export function useModules(programId: string | number) {
  const [rows, setRows] = useState<ModuleRow[]>(padRows([]))
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [lastSaved, setLastSaved] = useState<Date | null>(null)

  useEffect(() => {
    let cancelled = false
    api.listModules(programId).then(modules => {
      if (cancelled) return
      const converted: ModuleRow[] = modules.map(m => ({
        name:              m.name,
        description:       m.description ?? '',
        rationale:         m.rationale ?? '',
        key_interfaces:    m.key_interfaces ?? '',
        standards:         m.standards ?? '',
        tech_risk:         m.tech_risk,
        obsolescence_risk: m.obsolescence_risk,
        cots_candidate:    m.cots_candidate,
        future_recompete:  m.future_recompete,
      }))
      setRows(padRows(converted))
    }).catch(() => {
      // no modules yet — keep empty rows
    })
    return () => { cancelled = true }
  }, [programId])

  const updateRow = useCallback((index: number, field: keyof ModuleRow, value: string | boolean) => {
    setRows(prev => {
      const next = [...prev]
      next[index] = { ...next[index], [field]: value }
      return next
    })
  }, [])

  const addRow = useCallback(() => {
    setRows(prev => [...prev, { ...EMPTY_MODULE_ROW }])
  }, [])

  const removeRow = useCallback((index: number) => {
    setRows(prev => {
      const next = prev.filter((_, i) => i !== index)
      return padRows(next)
    })
  }, [])

  const save = useCallback(async (): Promise<boolean> => {
    const nonEmpty = rows.filter(r => r.name.trim())
    setSaveStatus('saving')
    try {
      const saved = await api.replaceModules(programId, nonEmpty)
      const converted: ModuleRow[] = saved.map(m => ({
        name:              m.name,
        description:       m.description ?? '',
        rationale:         m.rationale ?? '',
        key_interfaces:    m.key_interfaces ?? '',
        standards:         m.standards ?? '',
        tech_risk:         m.tech_risk,
        obsolescence_risk: m.obsolescence_risk,
        cots_candidate:    m.cots_candidate,
        future_recompete:  m.future_recompete,
      }))
      setRows(padRows(converted))
      setSaveStatus('saved')
      setLastSaved(new Date())
      return true
    } catch {
      setSaveStatus('error')
      return false
    }
  }, [rows, programId])

  const filledCount = rows.filter(r => r.name.trim()).length

  return { rows, updateRow, addRow, removeRow, save, saveStatus, lastSaved, filledCount }
}

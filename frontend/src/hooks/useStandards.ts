import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { StandardRow, SaveStatus } from '../types'
import { DEFAULT_STANDARD_ROWS } from '../types'

function toRows(data: Awaited<ReturnType<typeof api.listStandards>>): StandardRow[] {
  return data.map(s => ({
    standard_name:       s.standard_name,
    applies_to_modules:  s.applies_to_modules,
    applies_to_interfaces: s.applies_to_interfaces,
    catalog_id:          s.catalog_id,
    notes:               s.notes ?? '',
  }))
}

export function useStandards(programId: string | number) {
  const [rows, setRows]           = useState<StandardRow[]>(DEFAULT_STANDARD_ROWS.map(r => ({ ...r })))
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  useEffect(() => {
    let cancelled = false
    api.listStandards(programId).then(data => {
      if (cancelled) return
      // If the program already has saved rows, use them; otherwise keep the 4 defaults.
      if (data.length > 0) {
        setRows(toRows(data))
      }
      // length === 0 → leave the pre-seeded defaults in place (not saved yet)
    }).catch(() => {})
    return () => { cancelled = true }
  }, [programId])

  /** Toggle the "Modules" applicability checkbox for a row. */
  const toggleModules = useCallback((index: number) => {
    setRows(prev => prev.map((r, i) =>
      i === index ? { ...r, applies_to_modules: !r.applies_to_modules } : r
    ))
  }, [])

  /** Toggle the "Interfaces" applicability checkbox for a row. */
  const toggleInterfaces = useCallback((index: number) => {
    setRows(prev => prev.map((r, i) =>
      i === index ? { ...r, applies_to_interfaces: !r.applies_to_interfaces } : r
    ))
  }, [])

  const updateNotes = useCallback((index: number, notes: string) => {
    setRows(prev => prev.map((r, i) => i === index ? { ...r, notes } : r))
  }, [])

  /** Add a freeform (non-catalog) standard row. */
  const addCustomStandard = useCallback((name: string) => {
    setRows(prev => [...prev, {
      standard_name: name,
      applies_to_modules: false,
      applies_to_interfaces: false,
      catalog_id: null,
      notes: '',
    }])
  }, [])

  /** Only callable for custom rows (catalog_id === null). */
  const removeRow = useCallback((index: number) => {
    setRows(prev => prev.filter((_, i) => i !== index))
  }, [])

  const save = useCallback(async (): Promise<boolean> => {
    setSaveStatus('saving')
    try {
      const saved = await api.replaceStandards(programId, rows)
      setRows(toRows(saved))
      setSaveStatus('saved')
      return true
    } catch {
      setSaveStatus('error')
      return false
    }
  }, [rows, programId])

  const appliedCount = rows.filter(r => r.applies_to_modules || r.applies_to_interfaces).length

  return {
    rows,
    toggleModules,
    toggleInterfaces,
    updateNotes,
    addCustomStandard,
    removeRow,
    save,
    saveStatus,
    appliedCount,
  }
}

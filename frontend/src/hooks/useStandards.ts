import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { StandardRow, SaveStatus } from '../types'
import { STANDARDS_CATALOG } from '../data/standardsCatalog'

export function useStandards(programId: string | number) {
  const [rows, setRows] = useState<StandardRow[]>([])
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  useEffect(() => {
    let cancelled = false
    api.listStandards(programId).then(data => {
      if (cancelled) return
      if (data.length > 0) {
        setRows(data.map(s => ({
          standard_name: s.standard_name,
          applies:       s.applies,
          catalog_id:    s.catalog_id,
          notes:         s.notes ?? '',
        })))
      } else {
        // Pre-populate with catalog defaults (applies = false)
        setRows(
          STANDARDS_CATALOG.map(entry => ({
            standard_name: entry.name,
            applies:       false,
            catalog_id:    entry.catalog_id,
            notes:         '',
          }))
        )
      }
    }).catch(() => {})
    return () => { cancelled = true }
  }, [programId])

  const toggleApplies = useCallback((index: number) => {
    setRows(prev => prev.map((r, i) => i === index ? { ...r, applies: !r.applies } : r))
  }, [])

  const updateNotes = useCallback((index: number, notes: string) => {
    setRows(prev => prev.map((r, i) => i === index ? { ...r, notes } : r))
  }, [])

  const addCustomStandard = useCallback((name: string) => {
    setRows(prev => [...prev, { standard_name: name, applies: true, catalog_id: null, notes: '' }])
  }, [])

  const removeRow = useCallback((index: number) => {
    setRows(prev => prev.filter((_, i) => i !== index))
  }, [])

  const save = useCallback(async (): Promise<boolean> => {
    setSaveStatus('saving')
    try {
      await api.replaceStandards(programId, rows)
      setSaveStatus('saved')
      return true
    } catch {
      setSaveStatus('error')
      return false
    }
  }, [rows, programId])

  const appliedCount = rows.filter(r => r.applies).length

  return { rows, toggleApplies, updateNotes, addCustomStandard, removeRow, save, saveStatus, appliedCount }
}

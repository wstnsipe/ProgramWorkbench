import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { StandardRow, SaveStatus } from '../types'

function toRows(data: Awaited<ReturnType<typeof api.listStandards>>): StandardRow[] {
  return data.map(s => ({
    module_name:        s.module_name ?? null,
    standard_name:      s.standard_name,
    applies_to_modules: s.applies_to_modules,
    catalog_id:         s.catalog_id,
    notes:              s.notes ?? '',
  }))
}

export function useStandards(programId: string | number) {
  const [rows, setRows]             = useState<StandardRow[]>([])
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  useEffect(() => {
    let cancelled = false
    api.listStandards(programId).then(data => {
      if (cancelled) return
      setRows(toRows(data))
    }).catch(() => {})
    return () => { cancelled = true }
  }, [programId])

  /**
   * Replace the full set of standards for one module.
   * Each entry in `standards` is { name, catalog_id }.
   */
  const setModuleStandards = useCallback((
    moduleName: string,
    standards: { name: string; catalog_id: string | null }[],
  ) => {
    setRows(prev => {
      const without = prev.filter(r => r.module_name !== moduleName)
      const added: StandardRow[] = standards.map(s => ({
        module_name:        moduleName,
        standard_name:      s.name,
        applies_to_modules: true,
        catalog_id:         s.catalog_id,
        notes:              '',
      }))
      return [...without, ...added]
    })
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

  return { rows, setModuleStandards, save, saveStatus }
}

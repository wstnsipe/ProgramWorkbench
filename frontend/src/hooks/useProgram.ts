import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { Program, SaveStatus } from '../types'

export function useProgram(programId: string | number) {
  const [program, setProgram] = useState<Program | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')

  useEffect(() => {
    let cancelled = false
    api.getProgram(programId)
      .then(p => { if (!cancelled) setProgram(p) })
      .catch(err => { if (!cancelled) setLoadError(err.message ?? 'Failed to load program') })
    return () => { cancelled = true }
  }, [programId])

  const updateServiceBranch = useCallback(async (
    service_branch: Program['service_branch'],
    army_pae?: string | null,
  ) => {
    if (!program) return
    setProgram(prev => prev
      ? { ...prev, service_branch, army_pae: army_pae ?? null }
      : prev
    )
    setSaveStatus('saving')
    try {
      const updated = await api.updateProgram(programId, {
        service_branch,
        army_pae: army_pae ?? null,
      })
      setProgram(updated)
      setSaveStatus('saved')
    } catch {
      setSaveStatus('error')
    }
  }, [program, programId])

  return { program, setProgram, loadError, saveStatus, updateServiceBranch }
}

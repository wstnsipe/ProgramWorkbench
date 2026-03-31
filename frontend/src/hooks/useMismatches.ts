import { useState, useEffect, useCallback } from 'react'
import * as api from '../api'
import type { RuleViolation } from '../types'

/**
 * Fetches scenario-to-module consistency warnings from the backend.
 * Loads on mount and re-fetches when `refresh()` is called (e.g. after save).
 */
export function useMismatches(programId: string | number) {
  const [violations, setViolations] = useState<RuleViolation[]>([])

  const refresh = useCallback(() => {
    api.listMismatches(programId)
      .then(setViolations)
      .catch(() => {})
  }, [programId])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { violations, refresh }
}

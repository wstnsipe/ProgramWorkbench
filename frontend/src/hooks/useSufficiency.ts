import { useState, useCallback } from 'react'
import * as api from '../api'
import type { SufficiencyResult } from '../types'

/**
 * Lazy sufficiency hook — only fetches when refresh() is called.
 * Components can call refresh() after any save to get updated score.
 */
export function useSufficiency(programId: string | number) {
  const [result, setResult] = useState<SufficiencyResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getSufficiency(programId)
      setResult(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load sufficiency'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [programId])

  return { result, loading, error, refresh }
}

import { useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL

export interface PrefillSuggestion {
  field: string
  label: string
  suggested_value: string
  confidence: 'high' | 'low'
  source_excerpt: string
}

export function usePrefill(programId: string) {
  const [suggestions, setSuggestions] = useState<PrefillSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  async function fetchPrefill() {
    setLoading(true)
    try {
      const res = await fetch(`${API}/programs/${programId}/prefill`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        setSuggestions(data.suggestions ?? [])
        setDismissed(new Set())
      }
    } finally {
      setLoading(false)
    }
  }

  function dismiss(field: string) {
    setDismissed(prev => new Set(prev).add(field))
  }

  function accept(field: string) {
    dismiss(field)
  }

  function getSuggestion(field: string): PrefillSuggestion | null {
    if (dismissed.has(field)) return null
    return suggestions.find(s => s.field === field) ?? null
  }

  return {
    fetchPrefill,
    getSuggestion,
    dismiss,
    accept,
    loading,
    totalCount: suggestions.length,
    activeCount: suggestions.filter(s => !dismissed.has(s.field)).length,
  }
}

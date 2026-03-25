import { useState, useEffect } from 'react'

const API = import.meta.env.VITE_API_BASE_URL

export interface EvidenceChunk {
  source_filename: string
  text: string
  score: number
}

export interface EvidenceData {
  context: string
  chunks: EvidenceChunk[]
  has_docs: boolean
}

export function useEvidence(programId: string, context: string, enabled: boolean) {
  const [data, setData] = useState<EvidenceData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!enabled) return
    setData(null)
    setLoading(true)
    fetch(`${API}/programs/${programId}/evidence?context=${context}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => setData(d))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [programId, context, enabled])

  return { data, loading }
}

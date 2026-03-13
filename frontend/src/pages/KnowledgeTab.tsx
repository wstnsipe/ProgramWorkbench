import { useState, useEffect, type KeyboardEvent } from 'react'
import '../App.css'
import Button from '../components/Button'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface TopFile {
  file_id: number
  filename: string
  chunk_count: number
}

interface KnowledgeStatus {
  program_id: number
  file_count: number
  text_file_count: number
  chunk_count: number
  last_indexed_at: string | null
  top_files: TopFile[]
}

interface RetrieveResult {
  chunk_text: string
  file_id: number
  filename: string
  chunk_index: number
  source_type: string
  score: number
}

export default function KnowledgeTab({ programId }: { programId: string }) {
  const [status, setStatus] = useState<KnowledgeStatus | null>(null)
  const [loadErr, setLoadErr] = useState('')
  const [indexing, setIndexing] = useState(false)
  const [toast, setToast] = useState<{ kind: 'success' | 'error' | 'info'; message: string } | null>(null)

  const [query, setQuery] = useState('')
  const [retrieving, setRetrieving] = useState(false)
  const [results, setResults] = useState<RetrieveResult[] | null>(null)

  async function fetchStatus() {
    setLoadErr('')
    try {
      const res = await fetch(`${API}/programs/${programId}/knowledge/status`)
      if (res.ok) setStatus(await res.json())
      else setLoadErr('Failed to load knowledge status')
    } catch {
      setLoadErr('Network error')
    }
  }

  useEffect(() => { fetchStatus() }, [programId])

  async function handleReindex() {
    setIndexing(true)
    setToast({ kind: 'info', message: 'Re-indexing knowledge…' })
    try {
      const res = await fetch(`${API}/programs/${programId}/knowledge/index`, { method: 'POST' })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setToast({ kind: 'error', message: `Indexing failed: ${body.detail ?? res.statusText}` })
        return
      }
      const data: KnowledgeStatus = await res.json()
      setStatus(data)
      setToast({ kind: 'success', message: `Indexed ${data.chunk_count} chunks across ${data.file_count} file${data.file_count !== 1 ? 's' : ''}` })
    } catch {
      setToast({ kind: 'error', message: 'Indexing failed: Network error' })
    } finally {
      setIndexing(false)
    }
  }

  async function handleRetrieve() {
    const q = query.trim()
    if (!q) return
    setRetrieving(true)
    setResults(null)
    try {
      const res = await fetch(
        `${API}/programs/${programId}/knowledge/retrieve?q=${encodeURIComponent(q)}&k=6`
      )
      if (res.ok) {
        const data = await res.json()
        setResults(data.results ?? [])
      } else {
        const body = await res.json().catch(() => ({}))
        setToast({ kind: 'error', message: body.detail ?? 'Retrieve failed' })
      }
    } catch {
      setToast({ kind: 'error', message: 'Retrieve failed: Network error' })
    } finally {
      setRetrieving(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleRetrieve()
  }

  return (
    <div className="knowledge-tab">

      {/* ── Status panel ─────────────────────────────────────────── */}
      <section className="tab-section">
        <div className="tab-section__header">
          <p className="tab-section__title">Index Status</p>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleReindex}
            loading={indexing}
            disabled={indexing}
          >
            {indexing ? 'Re-indexing…' : 'Re-index Knowledge'}
          </Button>
        </div>

        {loadErr && <p className="error">{loadErr}</p>}

        {status && (
          <>
            <div className="kh-stats">
              <div className="kh-stat">
                <span className="kh-stat__value">{status.file_count}</span>
                <span className="kh-stat__label">Files Uploaded</span>
              </div>
              <div className="kh-stat">
                <span className="kh-stat__value">{status.text_file_count}</span>
                <span className="kh-stat__label">Text Extracted</span>
              </div>
              <div className="kh-stat">
                <span className="kh-stat__value">{status.chunk_count}</span>
                <span className="kh-stat__label">Indexed Chunks</span>
              </div>
              <div className="kh-stat kh-stat--wide">
                <span className={`kh-stat__value${status.last_indexed_at ? ' kh-stat__value--date' : ''}`}>
                  {status.last_indexed_at
                    ? new Date(status.last_indexed_at).toLocaleString()
                    : '—'}
                </span>
                <span className="kh-stat__label">Last Indexed</span>
              </div>
            </div>

            {status.chunk_count === 0 && (
              <div className="kh-hint">
                No chunks indexed yet. Upload documents then click <strong>Re-index Knowledge</strong>.
              </div>
            )}

            {status.top_files.length > 0 && (
              <div>
                <p className="kh-section-label">Top Source Files</p>
                <div className="kh-file-list">
                  {status.top_files.map(f => (
                    <div key={f.file_id} className="kh-file-row">
                      <span className="kh-file-row__name">📄 {f.filename}</span>
                      <span className="kh-file-row__count">{f.chunk_count} chunks</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {/* ── Retrieve preview ─────────────────────────────────────── */}
      <section className="tab-section" style={{ borderTop: '1px solid var(--border)', paddingTop: 20 }}>
        <div className="tab-section__header">
          <p className="tab-section__title">Retrieve Preview</p>
        </div>
        <p className="tab-section__desc" style={{ marginTop: 0 }}>
          Vector similarity search over indexed chunks (top 6).
        </p>

        <div className="search-row">
          <input
            type="text"
            className="search-input"
            placeholder="Enter a query to test retrieval…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <Button
            variant="secondary"
            onClick={handleRetrieve}
            disabled={!query.trim() || retrieving}
            loading={retrieving}
          >
            {retrieving ? 'Searching…' : 'Search'}
          </Button>
        </div>

        {results !== null && (
          results.length === 0 ? (
            <div className="empty-state empty-state--centered" style={{ paddingTop: 24, paddingBottom: 24 }}>
              <div className="empty-state__icon">🔍</div>
              <p className="empty-state__title">No results</p>
              <p className="empty-state__desc">No indexed chunks matched. Try re-indexing first.</p>
            </div>
          ) : (
            <div className="search-results">
              {results.map((r, i) => (
                <div key={i} className="search-result-item">
                  <div className="search-result-header">
                    <span className="search-result-filename">{r.filename}</span>
                    <span className="kh-score-badge">
                      {r.score.toFixed(3)}
                    </span>
                  </div>
                  <p className="search-result-snippet">
                    {r.chunk_text.slice(0, 200)}{r.chunk_text.length > 200 ? '…' : ''}
                  </p>
                </div>
              ))}
            </div>
          )
        )}
      </section>

      {toast && (
        <Toast kind={toast.kind} message={toast.message} onDismiss={() => setToast(null)} />
      )}
    </div>
  )
}

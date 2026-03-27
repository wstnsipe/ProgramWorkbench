import { useState, useEffect, useCallback } from 'react'
import '../App.css'
import Badge from '../components/Badge'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface DocumentRecord {
  id: number
  program_id: number
  doc_type: string
  file_path: string
  created_at: string
}

interface Props {
  programId: string
}

async function downloadBlob(res: Response, fallbackName: string) {
  const disposition = res.headers.get('Content-Disposition') ?? ''
  const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
  const filename = match ? match[1].replace(/['"]/g, '').trim() : fallbackName
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function DocumentsTab({ programId }: Props) {
  const [docs, setDocs] = useState<DocumentRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<string | null>(null)
  const [toast, setToast] = useState<{ kind: 'success' | 'error' | 'info'; message: string } | null>(null)
  const [showLegacy, setShowLegacy] = useState(false)

  const fetchDocs = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/programs/${programId}/documents`)
      if (!res.ok) throw new Error('Failed to load documents')
      setDocs(await res.json())
    } catch (e: unknown) {
      setToast({ kind: 'error', message: e instanceof Error ? e.message : 'Failed to load documents' })
    } finally {
      setLoading(false)
    }
  }, [programId])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  async function generateDoc(docType: string) {
    setGenerating(docType)
    setToast(null)
    try {
      // Start generation — returns job_id immediately (202 Accepted)
      const startRes = await fetch(`${API}/programs/${programId}/documents/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doc_type: docType }),   // singular doc_type, not doc_types array
      })
      if (!startRes.ok) {
        const data = await startRes.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to start generation')
      }
      const { job_id } = await startRes.json()

      // Poll until done or error (max 3 minutes)
      const deadline = Date.now() + 3 * 60 * 1000
      while (Date.now() < deadline) {
        await new Promise(r => setTimeout(r, 3000))
        const pollRes = await fetch(
          `${API}/programs/${programId}/documents/jobs/${job_id}`
        )
        if (!pollRes.ok) break
        const job = await pollRes.json()
        if (job.status === 'done') {
          await fetchDocs()
          setToast({ kind: 'success', message: 'Document generated' })
          return
        }
        if (job.status === 'error') {
          throw new Error(job.error || 'Generation failed')
        }
        // status === 'queued' or 'generating' — keep polling
      }
      throw new Error('Generation timed out')
    } catch (e: unknown) {
      setToast({ kind: 'error', message: e instanceof Error ? e.message : 'Generation failed' })
    } finally {
      setGenerating(null)
    }
  }

  async function generateSmartDoc(
    endpoint: string,
    key: string,
    label: string,
    fallbackFilename: string
  ) {
    setGenerating(key)
    setToast(null)
    try {
      const res = await fetch(endpoint, { method: 'POST' })
      if (res.status !== 200) {
        const text = await res.text()
        throw new Error(text || `${label} generation failed`)
      }
      await downloadBlob(res, fallbackFilename)
      await fetchDocs()
      setToast({ kind: 'success', message: `${label} generated and downloaded` })
    } catch (e: unknown) {
      setToast({ kind: 'error', message: e instanceof Error ? e.message : `${label} generation failed` })
    } finally {
      setGenerating(null)
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleString()
  }

  function formatDocType(docType: string) {
    const labels: Record<string, string> = {
      RFI:                         'RFI',
      RFI_SMART:                   'RFI',
      ACQ_STRATEGY:                'Acq Strategy',
      ACQ_STRATEGY_SMART:          'Acq Strategy',
      SEP:                         'SEP',
      SEP_SMART:                   'SEP',
      SEP_SMART_PLAN:              'SEP Plan (JSON)',
      MOSA_CONFORMANCE_PLAN:       'MOSA Plan',
      MOSA_CONFORMANCE_PLAN_SMART: 'MOSA Plan',
    }
    return labels[docType] ?? docType
  }

  function isSmartDoc(docType: string) {
    return docType.endsWith('_SMART')
  }

  const busy = generating !== null
  const base = `${API}/programs/${programId}`

  const sortedDocs = [...docs].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  const SMART_DOCS = [
    {
      key: 'RFI_SMART',
      name: 'RFI',
      label: 'Generate RFI',
      desc: 'AI-generated Request for Information tailored to your program requirements.',
      endpoint: `${base}/docs/rfi/smart`,
      fallback: 'RFI_Smart.docx',
    },
    {
      key: 'ACQ_STRATEGY_SMART',
      name: 'Acq Strategy',
      label: 'Generate Acq Strategy',
      desc: 'Acquisition Strategy aligned to your program objectives and constraints.',
      endpoint: `${base}/docs/acq_strategy/smart`,
      fallback: 'AcqStrategy_Smart.docx',
    },
    {
      key: 'SEP_SMART',
      name: 'SEP',
      label: 'Generate SEP',
      desc: 'Systems Engineering Plan built from your program data and wizard answers.',
      endpoint: `${base}/docs/sep/smart`,
      fallback: 'SEP_Smart.docx',
    },
    {
      key: 'MOSA_CONFORMANCE_PLAN_SMART',
      name: 'MOSA Plan',
      label: 'Generate MOSA Plan',
      desc: 'MOSA Conformance Plan addressing modular open systems standards.',
      endpoint: `${base}/docs/mosa_conformance/smart`,
      fallback: 'MOSAConformancePlan_Smart.docx',
    },
  ]

  const LEGACY_DOCS = [
    { key: 'RFI',                  label: 'RFI' },
    { key: 'ACQ_STRATEGY',         label: 'Acq Strategy' },
    { key: 'SEP',                  label: 'SEP' },
    { key: 'MOSA_CONFORMANCE_PLAN', label: 'MOSA Plan' },
  ]

  return (
    <div className="docs-page">

      {/* Page header */}
      <div className="docs-page-header">
        <h2 className="docs-page-title">Documents</h2>
        <p className="docs-page-desc">
          Generate AI-powered acquisition documents from your program data, uploaded files, and wizard answers.
        </p>
      </div>

      {/* Smart generator cards */}
      <section>
        <div className="docs-section-label">Smart Generators</div>
        <div className="doc-card-grid">
          {SMART_DOCS.map(doc => {
            const isThisBusy = generating === doc.key
            return (
              <div key={doc.key} className="doc-card">
                <div className="doc-card__header">
                  <span className="doc-card__name">{doc.name}</span>
                  <span className="doc-card__smart-badge">Smart</span>
                </div>
                <p className="doc-card__desc">{doc.desc}</p>
                <div className="doc-card__footer">
                  <button
                    className="doc-card__btn"
                    onClick={() => generateSmartDoc(doc.endpoint, doc.key, doc.label, doc.fallback)}
                    disabled={busy}
                  >
                    {isThisBusy
                      ? <><span className="doc-spinner" aria-hidden="true" />Generating…</>
                      : 'Generate'
                    }
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Legacy generators – collapsible */}
      <section>
        <button
          className="docs-legacy-toggle-btn"
          onClick={() => setShowLegacy(v => !v)}
          aria-expanded={showLegacy}
        >
          <span className={`docs-legacy-chevron${showLegacy ? ' docs-legacy-chevron--open' : ''}`}>
            ▸
          </span>
          Legacy Generators
        </button>
        {showLegacy && (
          <div className="docs-legacy-body">
            <div className="docs-legacy-grid">
              {LEGACY_DOCS.map(doc => (
                <button
                  key={doc.key}
                  className="btn-primary"
                  onClick={() => generateDoc(doc.key)}
                  disabled={busy}
                >
                  {generating === doc.key
                    ? <><span className="doc-spinner doc-spinner--light" aria-hidden="true" />Generating…</>
                    : doc.label
                  }
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Document history */}
      <section>
        <div className="docs-section-label">
          Generated Documents{docs.length > 0 ? ` (${docs.length})` : ''}
        </div>
        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : sortedDocs.length === 0 ? (
          <div className="empty-state">
            No documents yet. Use a Smart Generator above to create one.
          </div>
        ) : (
          <div className="docs-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Kind</th>
                  <th>Generated</th>
                  <th>Download</th>
                </tr>
              </thead>
              <tbody>
                {sortedDocs.map(doc => (
                  <tr key={doc.id}>
                    <td style={{ fontWeight: 500 }}>{formatDocType(doc.doc_type)}</td>
                    <td>
                      <Badge variant={isSmartDoc(doc.doc_type) ? 'smart' : 'legacy'}>
                        {isSmartDoc(doc.doc_type) ? 'Smart' : 'Legacy'}
                      </Badge>
                    </td>
                    <td className="docs-date-cell">{formatDate(doc.created_at)}</td>
                    <td>
                      <a
                        href={`${API}/documents/${doc.id}/download`}
                        download
                        className="download-link"
                      >
                        Download .docx
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {toast && (
        <Toast kind={toast.kind} message={toast.message} onDismiss={() => setToast(null)} />
      )}
    </div>
  )
}

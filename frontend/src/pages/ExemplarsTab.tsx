import { useState, useEffect, useRef, type DragEvent, type ChangeEvent } from 'react'
import '../App.css'
import Button from '../components/Button'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface Exemplar {
  id: number
  filename: string
  size_bytes: number
  uploaded_at: string
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return '📕'
  if (ext === 'docx' || ext === 'doc') return '📘'
  if (ext === 'md') return '📝'
  return '📄'
}

export default function ExemplarsTab({ programId }: { programId: string }) {
  const [exemplars, setExemplars] = useState<Exemplar[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [toast, setToast] = useState<{ kind: 'success' | 'error' | 'info'; message: string } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function fetchExemplars() {
    setLoading(true)
    try {
      const res = await fetch(`${API}/programs/${programId}/files?source_type=exemplar`)
      if (res.ok) setExemplars(await res.json())
    } catch {
      // network error — leave empty list
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchExemplars() }, [programId])

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragActive(true)
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragActive(false)
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) { setSelected(file); setToast(null) }
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    setSelected(e.target.files?.[0] ?? null)
    setToast(null)
  }

  function clearSelected() {
    setSelected(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  async function handleUpload() {
    if (!selected) return
    setUploading(true)
    setToast({ kind: 'info', message: 'Uploading exemplar…' })
    try {
      const form = new FormData()
      form.append('file', selected)
      const res = await fetch(`${API}/programs/${programId}/upload?source_type=exemplar`, {
        method: 'POST',
        body: form,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setToast({ kind: 'error', message: `Upload failed: ${body.detail ?? res.statusText}` })
        return
      }
      const name = selected.name
      clearSelected()
      await fetchExemplars()
      setToast({ kind: 'success', message: `"${name}" added as exemplar` })
    } catch {
      setToast({ kind: 'error', message: 'Upload failed: Network error' })
    } finally {
      setUploading(false)
    }
  }

  async function handleRemove(id: number, filename: string) {
    if (!window.confirm(`Remove "${filename}" from exemplars?`)) return
    const res = await fetch(`${API}/programs/${programId}/exemplars/${id}`, { method: 'DELETE' })
    if (!res.ok) { setToast({ kind: 'error', message: 'Remove failed' }); return }
    setExemplars(ex => ex.filter(e => e.id !== id))
    setToast({ kind: 'success', message: 'Exemplar removed' })
  }

  const dropZoneCls = [
    'drop-zone',
    dragActive ? 'drop-zone--active' : '',
    selected ? 'drop-zone--has-file' : '',
  ].filter(Boolean).join(' ')

  return (
    <div className="exemplars-tab">

      {/* Header */}
      <div>
        <p className="docs-section-label">Exemplar Documents</p>
        <p className="text-muted text-sm" style={{ marginTop: 4, lineHeight: 1.6 }}>
          Upload reference documents for the AI to follow as style and structure examples
          when generating acquisition artifacts.
        </p>
      </div>

      {/* Upload zone */}
      <section className="tab-section">
        <div className="tab-section__header">
          <p className="tab-section__title">Add Exemplar</p>
        </div>

        <div
          className={dropZoneCls}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !selected && inputRef.current?.click()}
        >
          <div className="drop-zone__icon">📋</div>
          <p className="drop-zone__text">
            Drag & drop or <span className="drop-zone__browse">browse to select</span>
          </p>
          <p className="drop-zone__hint">Accepted: .docx, .doc, .pdf, .txt, .md</p>
          <input
            ref={inputRef}
            type="file"
            accept=".docx,.doc,.pdf,.txt,.md"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </div>

        {selected && (
          <div className="drop-zone__selected">
            <span className="drop-zone__selected-name">
              {fileIcon(selected.name)}&nbsp;{selected.name}
            </span>
            <span className="text-muted text-sm">{formatBytes(selected.size)}</span>
            <button className="drop-zone__clear" onClick={clearSelected} title="Remove">×</button>
          </div>
        )}

        {selected && (
          <div className="form-actions">
            <Button onClick={handleUpload} disabled={uploading} loading={uploading}>
              {uploading ? 'Uploading…' : 'Add Exemplar'}
            </Button>
            <Button variant="secondary" onClick={clearSelected} disabled={uploading}>
              Cancel
            </Button>
          </div>
        )}
      </section>

      {/* Exemplar list */}
      <section className="tab-section">
        <div className="tab-section__header">
          <p className="tab-section__title">
            Exemplars{exemplars.length > 0 ? ` (${exemplars.length})` : ''}
          </p>
        </div>

        {loading ? (
          <div className="empty-state">Loading…</div>
        ) : exemplars.length === 0 ? (
          <div className="empty-state empty-state--centered">
            <div className="empty-state__icon">📋</div>
            <p className="empty-state__title">No exemplars yet</p>
            <p className="empty-state__desc">
              Add reference documents above to guide AI generation style and structure.
            </p>
          </div>
        ) : (
          <div className="exemplar-grid">
            {exemplars.map(ex => (
              <div key={ex.id} className="exemplar-card">
                <div className="exemplar-card__icon">{fileIcon(ex.filename)}</div>
                <div className="exemplar-card__name" title={ex.filename}>{ex.filename}</div>
                <div className="exemplar-card__meta">
                  {formatBytes(ex.size_bytes)} · {new Date(ex.uploaded_at).toLocaleDateString()}
                </div>
                <div className="exemplar-card__actions">
                  <Button variant="danger" size="sm" onClick={() => handleRemove(ex.id, ex.filename)}>
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {toast && (
        <Toast kind={toast.kind} message={toast.message} onDismiss={() => setToast(null)} />
      )}
    </div>
  )
}

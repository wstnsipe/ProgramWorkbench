import { useState, useEffect, useRef, type DragEvent, type ChangeEvent, type KeyboardEvent } from 'react'
import '../App.css'
import Button from '../components/Button'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface ProgramFile {
  id: number
  filename: string
  relative_path: string
  size_bytes: number
  uploaded_at: string
  extracted_text?: string | null
}

interface SearchResult {
  file_id: number
  filename: string
  match_count: number
  snippet: string
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

export default function UploadTab({ programId }: { programId: string }) {
  const [files, setFiles] = useState<ProgramFile[]>([])
  const [selected, setSelected] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [reextracting, setReextracting] = useState<number | null>(null)
  const [toast, setToast] = useState<{ kind: 'success' | 'error' | 'info'; message: string } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null)
  const [searching, setSearching] = useState(false)

  async function fetchFiles() {
    const res = await fetch(`${API}/programs/${programId}/files?source_type=program_input`)
    if (res.ok) setFiles(await res.json())
  }

  useEffect(() => { fetchFiles() }, [programId])

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
    setToast({ kind: 'info', message: 'Uploading…' })
    try {
      const form = new FormData()
      form.append('file', selected)
      const res = await fetch(`${API}/programs/${programId}/upload?source_type=program_input`, {
        method: 'POST',
        body: form,
      })
      await fetchFiles()
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setToast({ kind: 'error', message: `Upload failed: ${res.status} ${body.detail ?? res.statusText}` })
        return
      }
      clearSelected()
      setToast({ kind: 'success', message: `"${selected.name}" uploaded successfully` })
    } catch {
      await fetchFiles()
      setToast({ kind: 'error', message: 'Upload failed: Network error' })
    } finally {
      setUploading(false)
    }
  }

  async function handleReextract(fileId: number, filename: string) {
    setReextracting(fileId)
    try {
      const res = await fetch(`${API}/programs/${programId}/files/${fileId}/reextract`, {
        method: 'POST',
      })
      if (res.status === 404 || res.status === 405) {
        setToast({ kind: 'error', message: 'Re-extract is not yet available for this installation' })
        return
      }
      if (!res.ok) {
        setToast({ kind: 'error', message: `Re-extract failed for "${filename}"` })
        return
      }
      await fetchFiles()
      setToast({ kind: 'success', message: `Text re-extracted from "${filename}"` })
    } catch {
      setToast({ kind: 'error', message: 'Network error during re-extract' })
    } finally {
      setReextracting(null)
    }
  }

  async function handleSearch() {
    const q = searchQuery.trim()
    if (!q) return
    setSearching(true)
    setSearchResults(null)
    try {
      const res = await fetch(
        `${API}/programs/${programId}/knowledge/search?q=${encodeURIComponent(q)}&top_k=5`
      )
      if (res.ok) setSearchResults(await res.json())
      else setToast({ kind: 'error', message: 'Search failed' })
    } catch {
      setToast({ kind: 'error', message: 'Search failed: Network error' })
    } finally {
      setSearching(false)
    }
  }

  function handleSearchKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleSearch()
  }

  const dropZoneCls = [
    'drop-zone',
    dragActive ? 'drop-zone--active' : '',
    selected ? 'drop-zone--has-file' : '',
  ].filter(Boolean).join(' ')

  return (
    <div className="upload-tab">

      {/* Drop zone upload */}
      <section className="tab-section">
        <div className="tab-section__header">
          <p className="tab-section__title">Upload Document</p>
        </div>

        <div
          className={dropZoneCls}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !selected && inputRef.current?.click()}
        >
          <div className="drop-zone__icon">📂</div>
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
            <button className="drop-zone__clear" onClick={clearSelected} title="Remove file">×</button>
          </div>
        )}

        {selected && (
          <div className="form-actions">
            <Button
              onClick={handleUpload}
              disabled={!selected || uploading}
              loading={uploading}
            >
              {uploading ? 'Uploading…' : 'Upload'}
            </Button>
            <Button variant="secondary" onClick={clearSelected} disabled={uploading}>
              Cancel
            </Button>
          </div>
        )}
      </section>

      {/* Files table */}
      <section className="tab-section">
        <div className="tab-section__header">
          <p className="tab-section__title">
            Uploaded Files{files.length > 0 ? ` (${files.length})` : ''}
          </p>
        </div>

        {files.length === 0 ? (
          <div className="empty-state empty-state--centered">
            <div className="empty-state__icon">📁</div>
            <p className="empty-state__title">No files yet</p>
            <p className="empty-state__desc">Upload a document above to make it available for AI generation.</p>
          </div>
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th>Text Extracted</th>
                </tr>
              </thead>
              <tbody>
                {files.map(f => (
                  <tr key={f.id}>
                    <td style={{ fontWeight: 500 }}>
                      {fileIcon(f.filename)}&nbsp;{f.filename}
                    </td>
                    <td className="text-muted">{formatBytes(f.size_bytes)}</td>
                    <td className="text-muted" style={{ fontSize: 12 }}>
                      {new Date(f.uploaded_at).toLocaleString()}
                    </td>
                    <td>
                      {f.extracted_text ? (
                        <span className="extract-badge extract-badge--ok">✓ Extracted</span>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                          <span className="extract-badge extract-badge--none">Pending</span>
                          <button
                            className="row-action-btn"
                            onClick={() => handleReextract(f.id, f.filename)}
                            disabled={reextracting === f.id}
                            style={{ fontSize: 11 }}
                          >
                            {reextracting === f.id ? '…' : 'Re-extract'}
                          </button>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Search section */}
      <section className="tab-section" style={{ borderTop: '1px solid var(--border)', paddingTop: 20 }}>
        <div className="tab-section__header">
          <p className="tab-section__title">Search Uploads</p>
        </div>

        <div className="search-row">
          <input
            type="text"
            className="search-input"
            placeholder="Search across uploaded documents…"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
          />
          <Button
            variant="secondary"
            onClick={handleSearch}
            disabled={!searchQuery.trim() || searching}
            loading={searching}
          >
            {searching ? 'Searching…' : 'Search'}
          </Button>
        </div>

        {searchResults !== null && (
          searchResults.length === 0 ? (
            <div className="empty-state empty-state--centered" style={{ paddingTop: 32, paddingBottom: 32 }}>
              <div className="empty-state__icon">🔍</div>
              <p className="empty-state__title">No matches found</p>
              <p className="empty-state__desc">Try different keywords or upload more documents.</p>
            </div>
          ) : (
            <div className="search-results">
              {searchResults.map(r => (
                <div key={r.file_id} className="search-result-item">
                  <div className="search-result-header">
                    <span className="search-result-filename">{r.filename}</span>
                    <span className="search-result-count">
                      {r.match_count} match{r.match_count !== 1 ? 'es' : ''}
                    </span>
                  </div>
                  <p className="search-result-snippet">{r.snippet}</p>
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

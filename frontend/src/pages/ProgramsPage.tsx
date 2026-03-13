import { useState, useEffect, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import '../App.css'
import Button from '../components/Button'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface Program {
  id: number
  name: string
}

export default function ProgramsPage() {
  const [programs, setPrograms] = useState<Program[]>([])
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  async function fetchPrograms() {
    const res = await fetch(`${API}/programs`)
    if (!res.ok) { setError('Failed to load programs'); return }
    setPrograms(await res.json())
  }

  useEffect(() => { fetchPrograms() }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setSubmitting(true)
    setError('')
    try {
      const res = await fetch(`${API}/programs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.trim() }),
      })
      if (!res.ok) { setError('Failed to create program'); return }
      const created: Program = await res.json()
      setPrograms(prev => [created, ...prev])
      setName('')
    } catch {
      setError('Network error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="pgm-page">
      <div className="pgm-shell">
        <p className="pgm-subhead">ACQ WORKBENCH</p>
        <h1 className="pgm-heading">Programs</h1>

        <form onSubmit={handleSubmit} className="pgm-create-row" style={{ marginTop: '20px' }}>
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="New program name…"
            required
          />
          <Button type="submit" loading={submitting}>
            {submitting ? 'Adding…' : 'Add Program'}
          </Button>
        </form>

        {programs.length === 0 && !error ? (
          <p className="empty-state">No programs yet. Create one above.</p>
        ) : (
          <div className="pgm-list">
            {programs.map(p => (
              <div
                key={p.id}
                className="pgm-item"
                onClick={() => navigate(`/programs/${p.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && navigate(`/programs/${p.id}`)}
              >
                <span className="pgm-item-id">#{p.id}</span>
                <span className="pgm-item-name">{p.name}</span>
                <span className="pgm-item-arrow">→</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && (
        <Toast kind="error" message={error} onDismiss={() => setError('')} />
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import '../App.css'
import Button from '../components/Button'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface Module {
  id: number
  program_id: number
  name: string
  rationale: string | null
  key_interfaces: string | null
  standards: string | null
  tech_risk: boolean
  obsolescence_risk: boolean
  cots_candidate: boolean
  created_at: string
}

interface ModuleForm {
  name: string
  rationale: string
  key_interfaces: string
  standards: string
  tech_risk: boolean
  obsolescence_risk: boolean
  cots_candidate: boolean
}

const BLANK: ModuleForm = {
  name: '',
  rationale: '',
  key_interfaces: '',
  standards: '',
  tech_risk: false,
  obsolescence_risk: false,
  cots_candidate: false,
}

export default function ModulesTab({ programId }: { programId: string }) {
  const [modules, setModules] = useState<Module[]>([])
  const [loading, setLoading] = useState(true)
  const [seeding, setSeeding] = useState(false)
  const [editing, setEditing] = useState<Module | null>(null)
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState<ModuleForm>(BLANK)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ kind: 'success' | 'error' | 'info'; message: string } | null>(null)

  async function load() {
    setLoading(true)
    const res = await fetch(`${API}/programs/${programId}/modules`)
    if (!res.ok) {
      setToast({ kind: 'error', message: 'Failed to load modules' })
      setLoading(false)
      return
    }
    setModules(await res.json())
    setLoading(false)
  }

  useEffect(() => { load() }, [programId])

  function openAdd() {
    setEditing(null)
    setForm(BLANK)
    setAdding(true)
  }

  function openEdit(m: Module) {
    setAdding(false)
    setForm({
      name: m.name,
      rationale: m.rationale ?? '',
      key_interfaces: m.key_interfaces ?? '',
      standards: m.standards ?? '',
      tech_risk: m.tech_risk,
      obsolescence_risk: m.obsolescence_risk,
      cots_candidate: m.cots_candidate,
    })
    setEditing(m)
  }

  function closeModal() {
    setAdding(false)
    setEditing(null)
  }

  async function handleSave() {
    if (!form.name.trim()) return
    setSaving(true)
    const body = {
      name: form.name.trim(),
      rationale: form.rationale || null,
      key_interfaces: form.key_interfaces || null,
      standards: form.standards || null,
      tech_risk: form.tech_risk,
      obsolescence_risk: form.obsolescence_risk,
      cots_candidate: form.cots_candidate,
    }
    let res: Response
    if (editing) {
      res = await fetch(`${API}/programs/${programId}/modules/${editing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    } else {
      res = await fetch(`${API}/programs/${programId}/modules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    }
    setSaving(false)
    if (!res.ok) {
      setToast({ kind: 'error', message: 'Save failed' })
      return
    }
    closeModal()
    load()
    setToast({ kind: 'success', message: editing ? 'Module updated' : 'Module added' })
  }

  async function handleDelete(id: number) {
    if (!window.confirm('Delete this module?')) return
    const res = await fetch(`${API}/programs/${programId}/modules/${id}`, { method: 'DELETE' })
    if (!res.ok) { setToast({ kind: 'error', message: 'Delete failed' }); return }
    load()
    setToast({ kind: 'success', message: 'Module deleted' })
  }

  async function handleSeed() {
    setSeeding(true)
    const res = await fetch(`${API}/programs/${programId}/modules/seed`, { method: 'POST' })
    setSeeding(false)
    if (!res.ok) { setToast({ kind: 'error', message: 'Seed failed' }); return }
    const data: Module[] = await res.json()
    setModules(data)
    setToast({ kind: 'success', message: `Seeded ${data.length} module${data.length !== 1 ? 's' : ''} from Wizard` })
  }

  const showModal = adding || editing !== null

  return (
    <div className="modules-tab">

      {/* Toolbar — only shown when modules exist */}
      {!loading && modules.length > 0 && (
        <div className="modules-toolbar">
          <Button onClick={openAdd}>+ Add Module</Button>
          <Button
            variant="secondary"
            onClick={handleSeed}
            loading={seeding}
            disabled={seeding}
          >
            {seeding ? 'Seeding…' : 'Seed from Wizard'}
          </Button>
        </div>
      )}

      {loading ? (
        <div className="empty-state">Loading…</div>
      ) : modules.length === 0 ? (
        <div className="empty-state empty-state--centered">
          <div className="empty-state__icon">⬡</div>
          <p className="empty-state__title">No modules yet</p>
          <p className="empty-state__desc">
            Add modules manually or seed them automatically from your Wizard answers.
          </p>
          <div className="empty-state__actions">
            <Button onClick={openAdd}>+ Add Module</Button>
            <Button variant="secondary" onClick={handleSeed} loading={seeding} disabled={seeding}>
              {seeding ? 'Seeding…' : 'Seed from Wizard'}
            </Button>
          </div>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="modules-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Rationale</th>
                <th>Key Interfaces</th>
                <th>Standards</th>
                <th>Tech Risk</th>
                <th>Obs. Risk</th>
                <th>COTS</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {modules.map(m => (
                <tr key={m.id}>
                  <td className="modules-name-cell">{m.name}</td>
                  <td className="modules-text-cell" title={m.rationale ?? ''}>{m.rationale ?? '—'}</td>
                  <td className="modules-text-cell" title={m.key_interfaces ?? ''}>{m.key_interfaces ?? '—'}</td>
                  <td className="modules-text-cell" title={m.standards ?? ''}>{m.standards ?? '—'}</td>
                  <td className="modules-bool-cell">{m.tech_risk ? '✓' : ''}</td>
                  <td className="modules-bool-cell">{m.obsolescence_risk ? '✓' : ''}</td>
                  <td className="modules-bool-cell">{m.cots_candidate ? '✓' : ''}</td>
                  <td className="modules-actions-cell">
                    <button className="row-action-btn" onClick={() => openEdit(m)}>Edit</button>
                    <button className="row-action-btn danger" onClick={() => handleDelete(m.id)}>Del</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div
          className="modal-overlay"
          onClick={e => { if (e.target === e.currentTarget) closeModal() }}
        >
          <div className="modal">
            <h2 className="modal-title">{editing ? 'Edit Module' : 'Add Module'}</h2>
            <div className="brief-form">
              <div className="form-field">
                <label>Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="Module name"
                  autoFocus
                />
              </div>
              <div className="form-field">
                <label>Rationale</label>
                <p className="field-helper">Why this module exists as a separate unit</p>
                <textarea
                  rows={3}
                  value={form.rationale}
                  onChange={e => setForm(f => ({ ...f, rationale: e.target.value }))}
                  placeholder="Why this module exists…"
                />
              </div>
              <div className="form-field">
                <label>Key Interfaces</label>
                <p className="field-helper">Interface standards, APIs, or integration points</p>
                <textarea
                  rows={2}
                  value={form.key_interfaces}
                  onChange={e => setForm(f => ({ ...f, key_interfaces: e.target.value }))}
                  placeholder="Interface standards, APIs…"
                />
              </div>
              <div className="form-field">
                <label>Standards</label>
                <p className="field-helper">Applicable technical standards or specifications</p>
                <textarea
                  rows={2}
                  value={form.standards}
                  onChange={e => setForm(f => ({ ...f, standards: e.target.value }))}
                  placeholder="Applicable standards…"
                />
              </div>
              <div>
                <p className="form-checks-label">Risk Flags</p>
                <div className="form-checks" style={{ marginTop: 8 }}>
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={form.tech_risk}
                      onChange={e => setForm(f => ({ ...f, tech_risk: e.target.checked }))}
                    />
                    Tech Risk
                  </label>
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={form.obsolescence_risk}
                      onChange={e => setForm(f => ({ ...f, obsolescence_risk: e.target.checked }))}
                    />
                    Obsolescence Risk
                  </label>
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={form.cots_candidate}
                      onChange={e => setForm(f => ({ ...f, cots_candidate: e.target.checked }))}
                    />
                    COTS Candidate
                  </label>
                </div>
              </div>
              <div className="form-actions">
                <Button
                  onClick={handleSave}
                  loading={saving}
                  disabled={saving || !form.name.trim()}
                >
                  {saving ? 'Saving…' : 'Save'}
                </Button>
                <Button variant="secondary" onClick={closeModal}>Cancel</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <Toast kind={toast.kind} message={toast.message} onDismiss={() => setToast(null)} />
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import '../App.css'
import Button from '../components/Button'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface ProgramBrief {
  program_description: string | null
  dev_cost_estimate: number | null
  production_unit_cost: number | null
  attritable: boolean | null
  sustainment_tail: boolean | null
  software_large_part: boolean | null
  mission_critical: boolean | null
  safety_critical: boolean | null
  updated_at: string
}

type FormState = {
  program_description: string
  dev_cost_estimate: string
  production_unit_cost: string
  attritable: boolean
  sustainment_tail: boolean
  software_large_part: boolean
  mission_critical: boolean
  safety_critical: boolean
}

const EMPTY_FORM: FormState = {
  program_description: '',
  dev_cost_estimate: '',
  production_unit_cost: '',
  attritable: false,
  sustainment_tail: false,
  software_large_part: false,
  mission_critical: false,
  safety_critical: false,
}

function briefToForm(brief: ProgramBrief): FormState {
  return {
    program_description: brief.program_description ?? '',
    dev_cost_estimate: brief.dev_cost_estimate != null ? String(brief.dev_cost_estimate) : '',
    production_unit_cost: brief.production_unit_cost != null ? String(brief.production_unit_cost) : '',
    attritable: brief.attritable ?? false,
    sustainment_tail: brief.sustainment_tail ?? false,
    software_large_part: brief.software_large_part ?? false,
    mission_critical: brief.mission_critical ?? false,
    safety_critical: brief.safety_critical ?? false,
  }
}

const BOOL_FIELDS: { name: keyof FormState; label: string; helper: string }[] = [
  {
    name: 'attritable',
    label: 'Attritable',
    helper: 'System can be sacrificed without unacceptable mission impact',
  },
  {
    name: 'sustainment_tail',
    label: 'Sustainment Tail',
    helper: 'Long-term logistics, maintenance, or support requirements',
  },
  {
    name: 'software_large_part',
    label: 'Software Large Part',
    helper: 'Software is a significant portion of system complexity',
  },
  {
    name: 'mission_critical',
    label: 'Mission Critical',
    helper: 'Failure would directly impact mission success',
  },
  {
    name: 'safety_critical',
    label: 'Safety Critical',
    helper: 'Failure could result in injury, loss of life, or major damage',
  },
]

export default function BriefTab({ programId }: { programId: string }) {
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    async function fetchBrief() {
      const res = await fetch(`${API}/programs/${programId}/brief`)
      if (res.status === 404) return
      if (res.ok) {
        const brief: ProgramBrief = await res.json()
        setForm(briefToForm(brief))
        setUpdatedAt(brief.updated_at)
      }
    }
    fetchBrief()
  }, [programId])

  function handleText(e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  function handleCheck(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.checked }))
  }

  async function handleSave() {
    setSaving(true)
    setToast(null)
    try {
      const payload = {
        program_description: form.program_description || null,
        dev_cost_estimate: form.dev_cost_estimate !== '' ? parseFloat(form.dev_cost_estimate) : null,
        production_unit_cost: form.production_unit_cost !== '' ? parseFloat(form.production_unit_cost) : null,
        attritable: form.attritable,
        sustainment_tail: form.sustainment_tail,
        software_large_part: form.software_large_part,
        mission_critical: form.mission_critical,
        safety_critical: form.safety_critical,
      }
      const res = await fetch(`${API}/programs/${programId}/brief`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setToast({ kind: 'error', message: body.detail ?? 'Save failed' })
        return
      }
      const brief: ProgramBrief = await res.json()
      setUpdatedAt(brief.updated_at)
      setToast({ kind: 'success', message: 'Brief saved' })
    } catch {
      setToast({ kind: 'error', message: 'Network error' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="brief-form">

      {/* Program Description */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Program Description</h3>
          <p className="form-card__desc">Describe the mission, objectives, and key characteristics of this program.</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <label htmlFor="program_description">Description</label>
            <textarea
              id="program_description"
              name="program_description"
              rows={5}
              value={form.program_description}
              onChange={handleText}
              placeholder="Describe the program, its mission, and key objectives…"
            />
          </div>
        </div>
      </div>

      {/* Cost Estimates */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Cost Estimates</h3>
          <p className="form-card__desc">Approximate program cost thresholds in millions of dollars.</p>
        </div>
        <div className="form-card__body">
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="dev_cost_estimate">Dev Cost Estimate ($M)</label>
              <p className="field-helper">Total development cost across all phases</p>
              <input
                id="dev_cost_estimate"
                name="dev_cost_estimate"
                type="number"
                min="0"
                step="any"
                value={form.dev_cost_estimate}
                onChange={handleText}
                placeholder="0.00"
              />
            </div>
            <div className="form-field">
              <label htmlFor="production_unit_cost">Production Unit Cost ($M)</label>
              <p className="field-helper">Per-unit cost at full production rate</p>
              <input
                id="production_unit_cost"
                name="production_unit_cost"
                type="number"
                min="0"
                step="any"
                value={form.production_unit_cost}
                onChange={handleText}
                placeholder="0.00"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Program Attributes */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Program Attributes</h3>
          <p className="form-card__desc">Select all characteristics that apply to this program.</p>
        </div>
        <div className="form-card__body">
          <div className="form-checks form-checks--grid">
            {BOOL_FIELDS.map(({ name, label, helper }) => (
              <label key={name} className="check-label check-label--with-helper">
                <input
                  type="checkbox"
                  name={name}
                  checked={form[name] as boolean}
                  onChange={handleCheck}
                />
                <div>
                  <div>{label}</div>
                  <p className="field-helper">{helper}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Save row */}
      <div className="form-actions">
        <Button onClick={handleSave} loading={saving}>
          {saving ? 'Saving…' : 'Save Brief'}
        </Button>
        {updatedAt && (
          <span className="save-status">
            Saved {new Date(updatedAt).toLocaleString()}
          </span>
        )}
      </div>

      {toast && (
        <Toast kind={toast.kind} message={toast.message} onDismiss={() => setToast(null)} />
      )}
    </div>
  )
}

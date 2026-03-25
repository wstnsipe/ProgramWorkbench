import { useState, useEffect } from 'react'
import '../App.css'
import Button from '../components/Button'
import Toast from '../components/Toast'
import ModuleListEditor from '../components/brief/ModuleListEditor'
import type { ModuleRow } from '../types'
import { EMPTY_MODULE_ROW } from '../types'

const API = import.meta.env.VITE_API_BASE_URL

// ── Types ─────────────────────────────────────────────────────────────────────

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

type BriefForm = {
  program_description: string
  dev_cost_estimate: string
  production_unit_cost: string
  attritable: boolean
  sustainment_tail: boolean
  software_large_part: boolean
  mission_critical: boolean
  safety_critical: boolean
}

const EMPTY_BRIEF: BriefForm = {
  program_description: '',
  dev_cost_estimate: '',
  production_unit_cost: '',
  attritable: false,
  sustainment_tail: false,
  software_large_part: false,
  mission_critical: false,
  safety_critical: false,
}

function briefToForm(brief: ProgramBrief): BriefForm {
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

const BOOL_FIELDS: { name: keyof BriefForm; label: string; helper: string }[] = [
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

// ── Main BriefTab ─────────────────────────────────────────────────────────────

const BASELINE_ROWS = 5

export default function BriefTab({ programId }: { programId: string }) {
  const [form, setForm] = useState<BriefForm>(EMPTY_BRIEF)
  const [wizardAnswers, setWizardAnswers] = useState<Record<string, string>>({})
  const [modules, setModules] = useState<ModuleRow[]>(
    Array.from({ length: BASELINE_ROWS }, () => ({ ...EMPTY_MODULE_ROW }))
  )
  const [mosarepoSearched, setMosarepoSearched] = useState('')
  const [updatedAt, setUpdatedAt] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    async function fetchAll() {
      const [briefRes, wizardRes, modulesRes] = await Promise.all([
        fetch(`${API}/programs/${programId}/brief`),
        fetch(`${API}/programs/${programId}/wizard`),
        fetch(`${API}/programs/${programId}/modules`),
      ])

      if (briefRes.ok) {
        const brief: ProgramBrief = await briefRes.json()
        setForm(briefToForm(brief))
        setUpdatedAt(brief.updated_at)
      }

      if (wizardRes.ok) {
        const wizard = await wizardRes.json()
        const answers: Record<string, string> = {}
        for (const [k, v] of Object.entries(wizard.answers as Record<string, unknown>)) {
          if (k !== 'modules' && typeof v === 'string') answers[k] = v
        }
        setWizardAnswers(answers)
        setMosarepoSearched((wizard.answers as Record<string, unknown>)['o_mosa_repo_searched'] as string ?? '')
      }

      if (modulesRes.ok) {
        const mods: Array<Record<string, unknown>> = await modulesRes.json()
        const loaded: ModuleRow[] = mods.map(m => ({
          name: String(m.name ?? ''),
          description: String(m.description ?? ''),
          rationale: String(m.rationale ?? ''),
          key_interfaces: String(m.key_interfaces ?? ''),
          standards: String(m.standards ?? ''),
          tech_risk: Boolean(m.tech_risk),
          obsolescence_risk: Boolean(m.obsolescence_risk),
          cots_candidate: Boolean(m.cots_candidate),
          future_recompete: Boolean(m.future_recompete),
        }))
        const padded = [...loaded]
        while (padded.length < BASELINE_ROWS) padded.push({ ...EMPTY_MODULE_ROW })
        setModules(padded)
      }
    }
    fetchAll()
  }, [programId])

  function handleText(e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  function handleCheck(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.checked }))
  }

  function handleWizardText(id: string, value: string) {
    setWizardAnswers(prev => ({ ...prev, [id]: value }))
  }

  function handleModuleUpdate(index: number, field: keyof ModuleRow, value: string | boolean) {
    setModules(prev => prev.map((row, i) => i === index ? { ...row, [field]: value } : row))
  }

  function handleModuleAdd() {
    setModules(prev => [...prev, { ...EMPTY_MODULE_ROW }])
  }

  function handleModuleRemove(index: number) {
    setModules(prev => prev.filter((_, i) => i !== index))
  }

  async function handleSave() {
    setSaving(true)
    setToast(null)
    try {
      const briefPayload = {
        program_description: form.program_description || null,
        dev_cost_estimate: form.dev_cost_estimate !== '' ? parseFloat(form.dev_cost_estimate) : null,
        production_unit_cost: form.production_unit_cost !== '' ? parseFloat(form.production_unit_cost) : null,
        attritable: form.attritable,
        sustainment_tail: form.sustainment_tail,
        software_large_part: form.software_large_part,
        mission_critical: form.mission_critical,
        safety_critical: form.safety_critical,
      }

      const wizardPayload: Record<string, unknown> = {
        // Mirror brief fields into wizard answers for document generation
        a_program_description: form.program_description || '',
        b_dev_cost_estimate: form.dev_cost_estimate || '',
        c_production_unit_cost: form.production_unit_cost || '',
        ...wizardAnswers,
        o_mosa_repo_searched: mosarepoSearched,
      }

      const [briefRes] = await Promise.all([
        fetch(`${API}/programs/${programId}/brief`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(briefPayload),
        }),
        fetch(`${API}/programs/${programId}/wizard`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers: wizardPayload }),
        }),
        fetch(`${API}/programs/${programId}/modules`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ modules }),
        }),
      ])

      if (!briefRes.ok) {
        const body = await briefRes.json().catch(() => ({}))
        setToast({ kind: 'error', message: body.detail ?? 'Save failed' })
        return
      }

      const brief: ProgramBrief = await briefRes.json()
      setUpdatedAt(brief.updated_at)
      setToast({ kind: 'success', message: 'Saved' })
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

      {/* Similar Previous Programs */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Similar Previous Programs or Analogous Systems</h3>
          <p className="form-card__desc">Identify any predecessor programs, analogous systems, or similar acquisition efforts that can inform cost, schedule, or technical baselines.</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <textarea
              rows={4}
              value={wizardAnswers['e_similar_previous_programs'] ?? ''}
              onChange={e => handleWizardText('e_similar_previous_programs', e.target.value)}
              placeholder="Describe analogous programs or systems…"
            />
          </div>
        </div>
      </div>

      {/* Technical Challenges */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Key Technical Challenges and Risk Areas</h3>
          <p className="form-card__desc">Describe known or anticipated technical challenges, technology readiness concerns, integration risks, and areas of significant program risk.</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <textarea
              rows={4}
              value={wizardAnswers['f_tech_challenges_and_risk_areas'] ?? ''}
              onChange={e => handleWizardText('f_tech_challenges_and_risk_areas', e.target.value)}
              placeholder="Describe technical challenges and risk areas…"
            />
          </div>
        </div>
      </div>

      {/* MOSA Scenarios */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Relevant MOSA Scenarios</h3>
          <p className="form-card__desc">Describe Modular Open Systems Approach scenarios — how modularity, open interfaces, and competitive upgrade strategies may be applied or are anticipated.</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <textarea
              rows={4}
              value={wizardAnswers['g_mosa_scenarios'] ?? ''}
              onChange={e => handleWizardText('g_mosa_scenarios', e.target.value)}
              placeholder="Describe relevant MOSA scenarios…"
            />
          </div>
        </div>
      </div>

      {/* Candidate Modules */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Candidate Modules</h3>
          <p className="form-card__desc">Add each functional module or subsystem being considered for the program architecture. Include a description and rationale for each.</p>
        </div>
        <div className="form-card__body">
          <ModuleListEditor
            rows={modules}
            onUpdate={handleModuleUpdate}
            onAdd={handleModuleAdd}
            onRemove={handleModuleRemove}
          />
        </div>
      </div>

      {/* Standards & Architectures by Module */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Known Standards and Architectures (by Module)</h3>
          <p className="form-card__desc">Map candidate modules to relevant open standards, reference architectures, or interface standards (e.g., FACE, VITA 65/SOSA, VICTORY, GVA, CMOSS).</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <textarea
              rows={4}
              value={wizardAnswers['i_known_standards_architectures_mapping'] ?? ''}
              onChange={e => handleWizardText('i_known_standards_architectures_mapping', e.target.value)}
              placeholder="Map modules to applicable standards and architectures…"
            />
          </div>
        </div>
      </div>

      {/* Obsolescence Candidates */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Known or Anticipated Obsolescence Candidates</h3>
          <p className="form-card__desc">Identify hardware components, software dependencies, or technologies at risk of obsolescence during the program lifecycle and any mitigation strategies.</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <textarea
              rows={4}
              value={wizardAnswers['j_obsolescence_candidates'] ?? ''}
              onChange={e => handleWizardText('j_obsolescence_candidates', e.target.value)}
              placeholder="Describe obsolescence risks and mitigations…"
            />
          </div>
        </div>
      </div>

      {/* Commercial Solutions */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Commercial Solutions by Module</h3>
          <p className="form-card__desc">Identify commercially available products, COTS/MOTS solutions, or open-source options applicable to each candidate module.</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <textarea
              rows={4}
              value={wizardAnswers['k_commercial_solutions_by_module'] ?? ''}
              onChange={e => handleWizardText('k_commercial_solutions_by_module', e.target.value)}
              placeholder="Describe commercial solutions available for each module…"
            />
          </div>
        </div>
      </div>

      {/* Software Standards & Architectures */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">Software Standards and Architectures</h3>
          <p className="form-card__desc">Identify applicable software standards, architectural frameworks, and best practices (e.g., FACE Technical Standard, POSIX, AUTOSAR, DO-178C, IEC 61508).</p>
        </div>
        <div className="form-card__body">
          <div className="form-field">
            <textarea
              rows={4}
              value={wizardAnswers['n_software_standards_architectures'] ?? ''}
              onChange={e => handleWizardText('n_software_standards_architectures', e.target.value)}
              placeholder="Describe applicable software standards and architectures…"
            />
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

      {/* MOSA Repository */}
      <div className="form-card">
        <div className="form-card__header">
          <h3 className="form-card__title">MOSA Repository Search</h3>
          <p className="form-card__desc">Indicate whether the DoD MOSA repository or similar government resources have been searched for existing solutions, standards, qualified products, or reusable components.</p>
        </div>
        <div className="form-card__body">
          <div className="wizard-options">
            {[
              { value: 'yes', label: 'Yes' },
              { value: 'no', label: 'No' },
            ].map(opt => (
              <label
                key={opt.value}
                className={`wizard-option${mosarepoSearched === opt.value ? ' selected' : ''}`}
              >
                <input
                  type="radio"
                  name="o_mosa_repo_searched"
                  value={opt.value}
                  checked={mosarepoSearched === opt.value}
                  onChange={() => setMosarepoSearched(opt.value)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Save row */}
      <div className="form-actions">
        <Button onClick={handleSave} loading={saving}>
          {saving ? 'Saving…' : 'Save'}
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

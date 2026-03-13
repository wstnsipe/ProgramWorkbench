import { useState, useEffect, useCallback } from 'react'
import '../App.css'
import Toast from '../components/Toast'

const API = import.meta.env.VITE_API_BASE_URL

interface QuestionOption {
  value: string
  label: string
}

interface Question {
  id: string
  prompt: string
  help: string
  type: 'textarea' | 'number' | 'select' | 'modules_builder'
  options?: QuestionOption[]
  missing: boolean
}

export interface ModuleItem {
  name: string
  description: string
  rationale: string
  interfaces: string
}

interface WizardData {
  questions: Question[]
  answers: Record<string, unknown>
  answered_count: number
  total_count: number
  percent_complete: number
}

interface Props {
  programId: string
}

const emptyDraft = (): ModuleItem => ({ name: '', description: '', rationale: '', interfaces: '' })

// ── Modules Builder ──────────────────────────────────────────────────────────

interface ModulesBuilderProps {
  modules: ModuleItem[]
  onChange: (modules: ModuleItem[]) => void
}

function ModulesBuilder({ modules, onChange }: ModulesBuilderProps) {
  const [draft, setDraft] = useState<ModuleItem>(emptyDraft())
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [nameError, setNameError] = useState(false)

  function setField(field: keyof ModuleItem, value: string) {
    setDraft(prev => ({ ...prev, [field]: value }))
    if (field === 'name' && value.trim()) setNameError(false)
  }

  function commitDraft() {
    if (!draft.name.trim()) { setNameError(true); return }
    if (editingIndex !== null) {
      onChange(modules.map((m, i) => i === editingIndex ? { ...draft } : m))
      setEditingIndex(null)
    } else {
      onChange([...modules, { ...draft }])
    }
    setDraft(emptyDraft())
    setNameError(false)
  }

  function startEdit(i: number) {
    setDraft({ ...modules[i] })
    setEditingIndex(i)
    setNameError(false)
  }

  function cancelEdit() {
    setDraft(emptyDraft())
    setEditingIndex(null)
    setNameError(false)
  }

  function deleteModule(i: number) {
    onChange(modules.filter((_, idx) => idx !== i))
    if (editingIndex === i) { setEditingIndex(null); setDraft(emptyDraft()) }
  }

  const isEditing = editingIndex !== null

  return (
    <div className="mb-form">
      {/* Form */}
      <div className="mb-form-fields">
        <div className="mb-field">
          <label className="mb-label">
            Module Name <span className="mb-required">*</span>
          </label>
          <input
            className={`mb-input${nameError ? ' mb-input-error' : ''}`}
            value={draft.name}
            onChange={e => setField('name', e.target.value)}
            placeholder="e.g. Core Software, Navigation System…"
          />
          {nameError && <span className="mb-error-msg">Name is required</span>}
        </div>

        <div className="mb-field">
          <label className="mb-label">Description</label>
          <textarea
            className="mb-textarea"
            value={draft.description}
            onChange={e => setField('description', e.target.value)}
            rows={2}
            placeholder="Brief description of what this module does…"
          />
        </div>

        <div className="mb-field">
          <label className="mb-label">Rationale / Why a module?</label>
          <textarea
            className="mb-textarea"
            value={draft.rationale}
            onChange={e => setField('rationale', e.target.value)}
            rows={2}
            placeholder="Why should this be a distinct module?"
          />
        </div>

        <div className="mb-field">
          <label className="mb-label">Likely Interfaces</label>
          <input
            className="mb-input"
            value={draft.interfaces}
            onChange={e => setField('interfaces', e.target.value)}
            placeholder="e.g. FACE, SOSA, MIL-STD-1553…"
          />
        </div>

        <div className="mb-form-actions">
          <button className="mb-add-btn" onClick={commitDraft}>
            {isEditing ? 'Update module' : '+ Add module'}
          </button>
          {isEditing && (
            <button className="mb-cancel-btn" onClick={cancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Module list */}
      {modules.length > 0 && (
        <div className="mb-list">
          <div className="mb-list-header">Added modules ({modules.length})</div>
          {modules.map((mod, i) => (
            <div
              key={i}
              className={`mb-module-row${editingIndex === i ? ' mb-module-row-editing' : ''}`}
            >
              <div className="mb-module-info">
                <span className="mb-module-name">{mod.name}</span>
                {mod.description && (
                  <span className="mb-module-detail">{mod.description}</span>
                )}
                {mod.rationale && (
                  <span className="mb-module-detail mb-module-rationale">↳ {mod.rationale}</span>
                )}
                {mod.interfaces && (
                  <span className="mb-module-detail mb-module-interfaces">⇄ {mod.interfaces}</span>
                )}
              </div>
              <div className="mb-module-actions">
                <button
                  className="mb-row-btn"
                  onClick={() => startEdit(i)}
                  disabled={isEditing && editingIndex !== i}
                >
                  Edit
                </button>
                <button
                  className="mb-row-btn mb-row-btn-danger"
                  onClick={() => deleteModule(i)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modules.length === 0 && (
        <div className="mb-empty">No modules added yet. Fill in the form above and click Add module.</div>
      )}
    </div>
  )
}

// ── Main WizardTab ───────────────────────────────────────────────────────────

export default function WizardTab({ programId }: Props) {
  const [data, setData] = useState<WizardData | null>(null)
  const [localAnswers, setLocalAnswers] = useState<Record<string, string>>({})
  const [localModules, setLocalModules] = useState<ModuleItem[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [loadError, setLoadError] = useState('')

  const load = useCallback(async () => {
    const res = await fetch(`${API}/programs/${programId}/wizard`)
    if (!res.ok) { setLoadError('Failed to load wizard'); return }
    const d: WizardData = await res.json()
    setData(d)

    const init: Record<string, string> = {}
    for (const [k, v] of Object.entries(d.answers)) {
      if (k !== 'modules' && typeof v === 'string') init[k] = v ?? ''
    }
    setLocalAnswers(init)

    const mods = d.answers['modules']
    if (Array.isArray(mods)) {
      setLocalModules(mods.map((m: Record<string, string>) => ({
        name: m.name || '',
        description: m.description || '',
        rationale: m.rationale || '',
        interfaces: m.interfaces || '',
      })))
    }

    const firstMissing = d.questions.findIndex(q => q.missing)
    setCurrentIndex(firstMissing === -1 ? 0 : firstMissing)
  }, [programId])

  useEffect(() => { load() }, [load])

  const save = useCallback(async (
    answers: Record<string, string>,
    modules: ModuleItem[],
  ) => {
    setSaveStatus('saving')
    const payload: Record<string, unknown> = { ...answers }
    if (modules.length > 0) payload['modules'] = modules
    const res = await fetch(`${API}/programs/${programId}/wizard`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: payload }),
    })
    if (!res.ok) { setSaveStatus('error'); return }
    const d: WizardData = await res.json()
    setData(d)
    setSaveStatus('saved')
    setTimeout(() => setSaveStatus('idle'), 2000)
  }, [programId])

  if (loadError) return (
    <div className="empty-state">
      <span style={{ color: 'var(--error)' }}>{loadError}</span>
    </div>
  )

  if (!data) return <div className="empty-state">Loading…</div>

  const { questions, answered_count, total_count, percent_complete } = data
  const question = questions[currentIndex]
  const answer = localAnswers[question.id] ?? ''

  function setAnswer(value: string) {
    setLocalAnswers(prev => ({ ...prev, [question.id]: value }))
  }

  async function handleNext() {
    await save(localAnswers, localModules)
    if (currentIndex < questions.length - 1) setCurrentIndex(i => i + 1)
  }

  function handleBack() {
    if (currentIndex > 0) setCurrentIndex(i => i - 1)
  }

  const isFirst = currentIndex === 0
  const isLast = currentIndex === questions.length - 1

  const saveBtnLabel =
    saveStatus === 'saving' ? 'Saving…'
    : saveStatus === 'saved'  ? 'Saved ✓'
    : saveStatus === 'error'  ? 'Error'
    : 'Save'

  // Dot "answered" state: for modules_builder, answered if modules exist
  function isDotAnswered(q: Question): boolean {
    if (q.type === 'modules_builder') return localModules.length > 0
    return !q.missing && !!localAnswers[q.id]
  }

  return (
    <div className="wizard">
      {/* Progress bar */}
      <div className="wizard-progress">
        <div className="wizard-progress-bar">
          <div
            className="wizard-progress-fill"
            style={{ width: `${percent_complete}%` }}
          />
        </div>
        <span className="wizard-progress-label">
          {answered_count}/{total_count} answered
        </span>
      </div>

      {/* Step indicator */}
      <div className="wizard-step-indicator">
        Question {currentIndex + 1} of {total_count}
      </div>

      {/* Question card */}
      <div className="wizard-card">
        <div className="wizard-question-header">
          <h2 className="wizard-question-prompt">{question.prompt}</h2>
          {question.missing && (
            <span className="wizard-missing-badge">Unanswered</span>
          )}
        </div>
        <p className="wizard-help">{question.help}</p>

        <div className="wizard-input-area">
          {question.type === 'textarea' && (
            <textarea
              className="wizard-textarea"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              rows={6}
              placeholder="Enter your answer…"
            />
          )}
          {question.type === 'number' && (
            <input
              type="number"
              className="wizard-number-input"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              placeholder="0.00"
              min="0"
              step="0.01"
            />
          )}
          {question.type === 'select' && question.options && (
            <div className="wizard-options">
              {question.options.map(opt => (
                <label
                  key={opt.value}
                  className={`wizard-option${answer === opt.value ? ' selected' : ''}`}
                >
                  <input
                    type="radio"
                    name={question.id}
                    value={opt.value}
                    checked={answer === opt.value}
                    onChange={() => setAnswer(opt.value)}
                  />
                  {opt.label}
                </label>
              ))}
            </div>
          )}
          {question.type === 'modules_builder' && (
            <ModulesBuilder
              modules={localModules}
              onChange={setLocalModules}
            />
          )}
        </div>
      </div>

      {/* Navigation */}
      <div className="wizard-nav">
        <button
          className="wizard-nav-btn secondary"
          onClick={handleBack}
          disabled={isFirst}
        >
          ← Back
        </button>

        <div className="wizard-nav-center">
          <div className="wizard-dots">
            {questions.map((q, i) => (
              <button
                key={q.id}
                className={`wizard-dot${i === currentIndex ? ' current' : ''}${isDotAnswered(q) ? ' answered' : ''}`}
                onClick={() => setCurrentIndex(i)}
                title={`Question ${i + 1}`}
              />
            ))}
          </div>
        </div>

        <div className="wizard-nav-right">
          <button
            className="wizard-nav-btn secondary"
            onClick={() => save(localAnswers, localModules)}
            disabled={saveStatus === 'saving'}
          >
            {saveBtnLabel}
          </button>
          {!isLast ? (
            <button
              className="wizard-nav-btn primary"
              onClick={handleNext}
              disabled={saveStatus === 'saving'}
            >
              Next →
            </button>
          ) : (
            <button
              className="wizard-nav-btn primary"
              onClick={() => save(localAnswers, localModules)}
              disabled={saveStatus === 'saving'}
            >
              {saveStatus === 'saving' ? 'Saving…' : 'Finish'}
            </button>
          )}
        </div>
      </div>

      {saveStatus === 'error' && (
        <Toast kind="error" message="Save failed. Please try again." onDismiss={() => setSaveStatus('idle')} />
      )}
    </div>
  )
}

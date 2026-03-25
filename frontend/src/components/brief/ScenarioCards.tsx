/**
 * ScenarioCards — editable list of MOSA scenario entries.
 *
 * Each card:
 * - Type selector (reprocure / reuse / recompete)
 * - Definition subtitle
 * - Module name field (auto-extracted from description)
 * - Description textarea with word count
 * - Remove button (when more than MIN cards)
 * - Add scenario button at bottom
 * - Info panel with examples
 */
import type { ScenarioType, ScenarioRow } from '../../types'
import { SCENARIO_LABELS, SCENARIO_DESCRIPTIONS } from '../../types'
import InfoPanel from '../ui/InfoPanel'

const SCENARIO_EXAMPLES: Record<ScenarioType, string> = {
  reprocure: 'For the Navigation module, the Government can reprocure from any FACE-compliant vendor using the published ICD, enabling competitive sourcing at re-procurement.',
  reuse:     'For the Mission Computer module, the Government may adapt the existing AN/UYQ-100 architecture to this platform by updating the hardware abstraction layer to the SOSA-compliant backplane.',
  recompete: 'For the EO/IR Sensor module, at contract expiration the Government will recompete using published interface specifications, allowing any qualified vendor to bid on the follow-on.',
}

const SCENARIO_TYPES: ScenarioType[] = ['reprocure', 'reuse', 'recompete']

const MIN_CARDS = 3
const MIN_WORDS = 30
const TARGET_WORDS = 75

interface Props {
  scenarios: ScenarioRow[]
  wordCounts: number[]
  onUpdate: (index: number, field: keyof ScenarioRow, value: string) => void
  onAdd: () => void
  onRemove: (index: number) => void
}

export default function ScenarioCards({ scenarios, wordCounts, onUpdate, onAdd, onRemove }: Props) {
  return (
    <div className="scenario-editor">
      <div className="scenario-cards">
        {scenarios.map((s, i) => {
          const words = wordCounts[i] ?? 0
          const tooShort = s.description.trim() && words < MIN_WORDS
          const healthy  = words >= TARGET_WORDS

          return (
            <div key={i} className="scenario-card">
              <div className="scenario-card__header">
                <div className="scenario-card__header-row">
                  <select
                    className="scenario-card__type-select"
                    value={s.scenario_type}
                    onChange={e => onUpdate(i, 'scenario_type', e.target.value)}
                    aria-label="Scenario type"
                  >
                    {SCENARIO_TYPES.map(t => (
                      <option key={t} value={t}>{SCENARIO_LABELS[t]}</option>
                    ))}
                  </select>
                  {i >= MIN_CARDS && (
                    <button
                      className="scenario-card__remove"
                      onClick={() => onRemove(i)}
                      title="Remove scenario"
                      aria-label="Remove scenario"
                    >
                      ×
                    </button>
                  )}
                </div>
                <p className="scenario-card__def">{SCENARIO_DESCRIPTIONS[s.scenario_type]}</p>
              </div>

              <div className="scenario-card__body">
                <div className="form-field">
                  <label className="field-label" htmlFor={`module-${i}`}>
                    Module name
                  </label>
                  <input
                    id={`module-${i}`}
                    className="scenario-card__module-input"
                    value={s.module_name}
                    onChange={e => onUpdate(i, 'module_name', e.target.value)}
                    placeholder="e.g. Navigation System"
                  />
                </div>

                <div className="form-field">
                  <label className="field-label" htmlFor={`desc-${i}`}>
                    Describe this scenario
                    <span className="field-label__helper">
                      Start with "For the [module name] module, …"
                    </span>
                  </label>
                  <textarea
                    id={`desc-${i}`}
                    className={`scenario-card__textarea${tooShort ? ' textarea--warn' : ''}`}
                    rows={5}
                    value={s.description}
                    onChange={e => onUpdate(i, 'description', e.target.value)}
                    placeholder={SCENARIO_EXAMPLES[s.scenario_type]}
                  />
                  <div className="scenario-card__footer">
                    <span className={`word-count${healthy ? ' word-count--ok' : tooShort ? ' word-count--warn' : ''}`}>
                      {words} / 100 words{healthy ? ' ✓' : tooShort ? ` (aim for ${TARGET_WORDS}+)` : ''}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <button className="scenario-cards__add-btn" onClick={onAdd}>
        + Add scenario
      </button>

      <InfoPanel variant="tip">
        Strong scenarios ground document generation. Reference the module name exactly as entered in Candidate Modules.
        Each scenario should describe a specific acquisition or lifecycle event (~75–100 words).
      </InfoPanel>
    </div>
  )
}

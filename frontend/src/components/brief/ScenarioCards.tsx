/**
 * ScenarioCards — three side-by-side cards for MOSA scenarios.
 *
 * Each card:
 * - Title (scenario type)
 * - Definition tooltip
 * - Module name field (auto-extracted from description)
 * - Description textarea with word count
 * - Example info panel
 */
import type { ScenarioType, ScenarioRow } from '../../types'
import { SCENARIO_LABELS, SCENARIO_DESCRIPTIONS } from '../../types'
import InfoPanel from '../ui/InfoPanel'

const SCENARIO_EXAMPLES: Record<ScenarioType, string> = {
  reprocure: 'For the Navigation module, the Government can reprocure from any FACE-compliant vendor using the published ICD, enabling competitive sourcing at re-procurement.',
  reuse:     'For the Mission Computer module, the Government may adapt the existing AN/UYQ-100 architecture to this platform by updating the hardware abstraction layer to SOSA-compliant backplane.',
  recompete: 'For the EO/IR Sensor module, at contract expiration the Government will recompete using published interface specifications, allowing any qualified vendor to bid on the follow-on.',
}

interface Props {
  scenarios: ScenarioRow[]
  wordCounts: Record<ScenarioType, number>
  onUpdate: (type: ScenarioType, field: keyof ScenarioRow, value: string) => void
}

const MIN_WORDS = 30
const TARGET_WORDS = 75

export default function ScenarioCards({ scenarios, wordCounts, onUpdate }: Props) {
  return (
    <div className="scenario-cards">
      {scenarios.map(s => {
        const words = wordCounts[s.scenario_type]
        const tooShort = s.description.trim() && words < MIN_WORDS
        const healthy  = words >= TARGET_WORDS

        return (
          <div key={s.scenario_type} className="scenario-card">
            <div className="scenario-card__header">
              <h4 className="scenario-card__title">{SCENARIO_LABELS[s.scenario_type]}</h4>
              <p className="scenario-card__def">{SCENARIO_DESCRIPTIONS[s.scenario_type]}</p>
            </div>

            <div className="scenario-card__body">
              <div className="form-field">
                <label className="field-label" htmlFor={`module-${s.scenario_type}`}>
                  Module name
                </label>
                <input
                  id={`module-${s.scenario_type}`}
                  className="scenario-card__module-input"
                  value={s.module_name}
                  onChange={e => onUpdate(s.scenario_type, 'module_name', e.target.value)}
                  placeholder="e.g. Navigation System"
                />
              </div>

              <div className="form-field">
                <label className="field-label" htmlFor={`desc-${s.scenario_type}`}>
                  Describe this scenario
                  <span className="field-label__helper">
                    Start with "For the [module name] module, …"
                  </span>
                </label>
                <textarea
                  id={`desc-${s.scenario_type}`}
                  className={`scenario-card__textarea ${tooShort ? 'textarea--warn' : ''}`}
                  rows={5}
                  value={s.description}
                  onChange={e => onUpdate(s.scenario_type, 'description', e.target.value)}
                  placeholder={SCENARIO_EXAMPLES[s.scenario_type]}
                />
                <div className="scenario-card__footer">
                  <span className={`word-count ${healthy ? 'word-count--ok' : tooShort ? 'word-count--warn' : ''}`}>
                    {words} words {words === 0 ? '' : healthy ? '✓' : tooShort ? `(aim for ${TARGET_WORDS}+)` : ''}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )
      })}

      <InfoPanel variant="tip">
        Strong scenarios ground document generation. Use the module name from your Candidate Modules table.
        Each scenario should describe a specific acquisition or lifecycle event.
      </InfoPanel>
    </div>
  )
}

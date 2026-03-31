/**
 * ScenarioTableEditor — MOSA Scenario input rows.
 *
 * Each scenario must follow the format:
 *   "For the [module name] module, the USG desires the ability to ..."
 *
 * Rows are labeled "MOSA Scenario #N".
 * 3 default rows, user can add more.
 * Lightbulb icon shows format examples — no auto-fill.
 */
import { useState } from 'react'
import type { ScenarioRow } from '../../types'

const BASELINE = 3

const MOSA_FORMAT_RE = /^For the .+ module, the USG desires the ability to /i

const MOSA_EXAMPLES = [
  'For the Navigation module, the USG desires the ability to REPAIR the module organically using the published ICD.',
  'For the Mission Computer module, the USG desires the ability to REMOVE and REPLACE the module with any SOSA-compliant alternative.',
  'For the EO/IR Sensor module, the USG desires the ability to MODIFY the module without impacting adjacent modules.',
]

function validateDescription(desc: string): string | null {
  const trimmed = desc.trim()
  if (!trimmed) return null
  if (!MOSA_FORMAT_RE.test(trimmed)) {
    return 'Must start with: "For the [module name] module, the USG desires the ability to …"'
  }
  return null
}

interface Props {
  rows: ScenarioRow[]
  onUpdate: (index: number, field: keyof ScenarioRow, value: string) => void
  onAdd: () => void
  onRemove: (index: number) => void
  baselineCount?: number
}

export default function ScenarioTableEditor({ rows, onUpdate, onAdd, onRemove, baselineCount = BASELINE }: Props) {
  const [showHelp, setShowHelp] = useState(false)

  return (
    <div className="module-table-wrap">
      <div className="scenario-help-row">
        <button
          className="scenario-help-btn"
          onClick={() => setShowHelp(v => !v)}
          aria-label="Show scenario format examples"
          title="Show format examples"
          type="button"
        >
          💡 Format help
        </button>
      </div>

      {showHelp && (
        <div className="scenario-help-popover">
          <strong>Required format:</strong>
          <p className="scenario-help-format">
            "For the [module name] module, the USG desires the ability to …"
          </p>
          <ul className="scenario-help-examples">
            {MOSA_EXAMPLES.map((ex, i) => (
              <li key={i}>{ex}</li>
            ))}
          </ul>
        </div>
      )}

      <table className="module-table">
        <thead>
          <tr>
            <th className="module-table__col-scenario-label">Scenario</th>
            <th className="module-table__col-text">Description</th>
            <th className="module-table__col-del" aria-label="Delete" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const error = validateDescription(row.description ?? '')
            const isEmpty = !(row.description ?? '').trim()
            return (
              <tr
                key={i}
                className={`module-table__row${isEmpty ? ' module-table__row--empty' : ''}${error ? ' module-table__row--invalid' : ''}`}
              >
                <td className="module-table__cell-scenario-label">
                  MOSA Scenario {i + 1}
                </td>
                <td>
                  <input
                    className={`module-table__input${error ? ' module-table__input--invalid' : ''}`}
                    value={row.description ?? ''}
                    onChange={e => onUpdate(i, 'description', e.target.value)}
                    placeholder="For the [module] module, the USG desires the ability to…"
                    aria-label={`MOSA Scenario ${i + 1}`}
                    aria-invalid={!!error}
                  />
                  {error && (
                    <span className="scenario-error" role="alert">{error}</span>
                  )}
                </td>
                <td className="module-table__cell-del">
                  {i >= baselineCount && (
                    <button
                      className="module-table__del-btn"
                      onClick={() => onRemove(i)}
                      aria-label={`Remove MOSA Scenario ${i + 1}`}
                      title="Remove row"
                    >
                      ×
                    </button>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <div className="module-table__footer">
        <button className="module-table__add-btn" onClick={onAdd}>
          + Add row
        </button>
      </div>
    </div>
  )
}

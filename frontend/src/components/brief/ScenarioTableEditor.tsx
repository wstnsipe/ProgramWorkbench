/**
 * ScenarioTableEditor — inline row-table for MOSA scenarios.
 *
 * Design (mirrors ModuleListEditor):
 * - 3 default rows (one per scenario type), always visible
 * - Only rows beyond baseline 3 are removable
 * - Columns: type selector + description (short text) + delete
 * - "Add row" button at bottom
 */
import type { ScenarioRow, ScenarioType } from '../../types'
import { SCENARIO_LABELS } from '../../types'
import InfoPanel from '../ui/InfoPanel'

const SCENARIO_TYPES: ScenarioType[] = ['reprocure', 'reuse', 'recompete']
const BASELINE = 3

const SCENARIO_EXAMPLES: Record<ScenarioType, string> = {
  reprocure: 'e.g. Nav module reprocured from any FACE-compliant vendor using the published ICD',
  reuse:     'e.g. Mission Computer adapted from AN/UYQ-100 with updated SOSA hardware abstraction layer',
  recompete: 'e.g. EO/IR Sensor recompeted at contract expiration using published interface specifications',
}

interface Props {
  rows: ScenarioRow[]
  onUpdate: (index: number, field: keyof ScenarioRow, value: string) => void
  onAdd: () => void
  onRemove: (index: number) => void
  baselineCount?: number
}

export default function ScenarioTableEditor({ rows, onUpdate, onAdd, onRemove, baselineCount = BASELINE }: Props) {
  return (
    <div className="module-table-wrap">
      <table className="module-table">
        <thead>
          <tr>
            <th className="module-table__col-name">Scenario Type</th>
            <th className="module-table__col-text">Description</th>
            <th className="module-table__col-del" aria-label="Delete" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`module-table__row ${row.description.trim() ? '' : 'module-table__row--empty'}`}
            >
              <td>
                <select
                  className="module-table__input module-table__input--name"
                  value={row.scenario_type}
                  onChange={e => onUpdate(i, 'scenario_type', e.target.value)}
                  aria-label={`Scenario ${i + 1} type`}
                >
                  {SCENARIO_TYPES.map(t => (
                    <option key={t} value={t}>{SCENARIO_LABELS[t]}</option>
                  ))}
                </select>
              </td>
              <td>
                <input
                  className="module-table__input"
                  value={row.description}
                  onChange={e => onUpdate(i, 'description', e.target.value)}
                  placeholder={SCENARIO_EXAMPLES[row.scenario_type]}
                  aria-label={`Scenario ${i + 1} description`}
                />
              </td>
              <td className="module-table__cell-del">
                {i >= baselineCount && (
                  <button
                    className="module-table__del-btn"
                    onClick={() => onRemove(i)}
                    aria-label={`Remove scenario ${i + 1}`}
                    title="Remove row"
                  >
                    ×
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="module-table__footer">
        <button className="module-table__add-btn" onClick={onAdd}>
          + Add row
        </button>
      </div>

      <InfoPanel variant="tip">
        Each scenario describes how a module can be reprocured, reused, or recompeted.
        Reference the exact module name as entered in Candidate Modules.
        Example: "For the Navigation module, the Government can reprocure from any FACE-compliant vendor using the published ICD."
      </InfoPanel>
    </div>
  )
}

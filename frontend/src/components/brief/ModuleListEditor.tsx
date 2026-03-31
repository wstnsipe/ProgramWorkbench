/**
 * ModuleListEditor — inline row-table replacing the draft/add/cancel pattern.
 *
 * Design:
 * - Always-visible rows (min 5), edit inline
 * - Checkbox columns: tech_risk, obsolescence_risk, cots_candidate, future_recompete
 * - "Add row" button at bottom
 * - Name is required (row highlight if non-empty name missing)
 */
import type { ModuleRow } from '../../types'
import InfoPanel from '../ui/InfoPanel'

const BASELINE = 5

interface Props {
  rows: ModuleRow[]
  onUpdate: (index: number, field: keyof ModuleRow, value: string | boolean) => void
  onAdd: () => void
  onRemove: (index: number) => void
  baselineCount?: number
}

const BOOL_COLS: { field: keyof ModuleRow; label: string; abbrev: string }[] = [
  { field: 'tech_risk',         label: 'Tech Risk',         abbrev: 'TR' },
  { field: 'obsolescence_risk', label: 'Obsolescence Risk', abbrev: 'OR' },
  { field: 'cots_candidate',    label: 'COTS Candidate',    abbrev: 'COTS' },
  { field: 'future_recompete',  label: 'Future Recompete',  abbrev: 'FC' },
]

export default function ModuleListEditor({ rows, onUpdate, onAdd, onRemove, baselineCount = BASELINE }: Props) {
  return (
    <div className="module-table-wrap">
      <table className="module-table">
        <thead>
          <tr>
            <th className="module-table__col-name">Module Name <span className="required-star">*</span></th>
            <th className="module-table__col-text">Description</th>
            <th className="module-table__col-text">Rationale</th>
            {BOOL_COLS.map(c => (
              <th key={c.field} className="module-table__col-check" title={c.label}>{c.abbrev}</th>
            ))}
            <th className="module-table__col-del" aria-label="Delete" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`module-table__row ${row.name.trim() ? '' : 'module-table__row--empty'}`}
            >
              <td>
                <input
                  className="module-table__input module-table__input--name"
                  value={row.name}
                  onChange={e => onUpdate(i, 'name', e.target.value)}
                  placeholder={`Module ${i + 1}`}
                  aria-label={`Module ${i + 1} name`}
                />
              </td>
              <td>
                <input
                  className="module-table__input"
                  value={row.description}
                  onChange={e => onUpdate(i, 'description', e.target.value)}
                  placeholder="Brief description"
                  aria-label={`Module ${i + 1} description`}
                />
              </td>
              <td>
                <input
                  className="module-table__input"
                  value={row.rationale}
                  onChange={e => onUpdate(i, 'rationale', e.target.value)}
                  placeholder="Why a module?"
                  aria-label={`Module ${i + 1} rationale`}
                />
              </td>
              {BOOL_COLS.map(c => (
                <td key={c.field} className="module-table__cell-check">
                  <input
                    type="checkbox"
                    checked={row[c.field] as boolean}
                    onChange={e => onUpdate(i, c.field, e.target.checked)}
                    aria-label={`${c.label} for module ${i + 1}`}
                    disabled={!row.name.trim()}
                  />
                </td>
              ))}
              <td className="module-table__cell-del">
                {i >= baselineCount && (
                  <button
                    className="module-table__del-btn"
                    onClick={() => onRemove(i)}
                    aria-label={`Remove module ${row.name || i + 1}`}
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
        <span className="module-table__legend">
          TR = Tech Risk · OR = Obsolescence Risk · COTS = Commercial Candidate · FC = Future Recompete
        </span>
      </div>

      <InfoPanel variant="tip">
        Checkboxes unlock document language. COTS adds commercial-first requirements.
        TR flags drive risk register entries. FC adds recompete strategy language.
      </InfoPanel>
    </div>
  )
}

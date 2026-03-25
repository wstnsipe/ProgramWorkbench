/**
 * StandardsEditor — name + applicability (Modules / Interfaces) table.
 *
 * Design:
 * - 4 default rows pre-seeded from DEFAULT_STANDARD_ROWS (catalog_id set, not removable)
 * - Each row: standard name | Modules ☑ | Interfaces ☑ | Notes | × (custom only)
 * - Add-custom row at the bottom
 */
import { useState } from 'react'
import type { StandardRow } from '../../types'

interface Props {
  rows: StandardRow[]
  onToggleModules:    (index: number) => void
  onToggleInterfaces: (index: number) => void
  onUpdateNotes:      (index: number, notes: string) => void
  onAddCustom:        (name: string) => void
  onRemove:           (index: number) => void
}

export default function StandardsEditor({
  rows,
  onToggleModules,
  onToggleInterfaces,
  onUpdateNotes,
  onAddCustom,
  onRemove,
}: Props) {
  const [customInput, setCustomInput] = useState('')

  function handleAddCustom() {
    const name = customInput.trim()
    if (!name) return
    onAddCustom(name)
    setCustomInput('')
  }

  return (
    <div className="standards-editor">
      <table className="standards-table">
        <thead>
          <tr>
            <th className="standards-table__col-name">Standard / Architecture</th>
            <th className="standards-table__col-cb" title="Applies to module boundaries">Modules</th>
            <th className="standards-table__col-cb" title="Applies to interface definitions">Interfaces</th>
            <th className="standards-table__col-notes">Notes</th>
            <th className="standards-table__col-del" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const active = row.applies_to_modules || row.applies_to_interfaces
            return (
              <tr
                key={i}
                className={`standards-table__row${active ? ' standards-table__row--active' : ''}`}
              >
                <td className="standards-table__name">
                  <span>{row.standard_name}</span>
                  {row.catalog_id && (
                    <span className="standards-table__catalog-id">{row.catalog_id}</span>
                  )}
                </td>

                <td className="standards-table__cb">
                  <input
                    type="checkbox"
                    checked={row.applies_to_modules}
                    onChange={() => onToggleModules(i)}
                    aria-label={`${row.standard_name} applies to modules`}
                  />
                </td>

                <td className="standards-table__cb">
                  <input
                    type="checkbox"
                    checked={row.applies_to_interfaces}
                    onChange={() => onToggleInterfaces(i)}
                    aria-label={`${row.standard_name} applies to interfaces`}
                  />
                </td>

                <td className="standards-table__notes">
                  <input
                    className="standards-table__notes-input"
                    value={row.notes}
                    onChange={e => onUpdateNotes(i, e.target.value)}
                    placeholder="Version, scope notes…"
                    aria-label={`Notes for ${row.standard_name}`}
                  />
                </td>

                <td className="standards-table__del">
                  {/* Only custom rows (no catalog_id) are removable */}
                  {!row.catalog_id && (
                    <button
                      className="standards-table__del-btn"
                      onClick={() => onRemove(i)}
                      aria-label={`Remove ${row.standard_name}`}
                      title="Remove"
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

      <div className="standards-editor__add-custom">
        <input
          className="standards-editor__custom-input"
          value={customInput}
          onChange={e => setCustomInput(e.target.value)}
          placeholder="Add standard (e.g., MIL-STD-810, VICTORY, DO-178C)"
          onKeyDown={e => e.key === 'Enter' && handleAddCustom()}
        />
        <button
          className="btn btn--secondary btn--sm"
          onClick={handleAddCustom}
          disabled={!customInput.trim()}
        >
          Add
        </button>
      </div>
    </div>
  )
}

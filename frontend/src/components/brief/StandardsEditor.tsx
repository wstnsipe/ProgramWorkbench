/**
 * StandardsEditor — Yes/No toggle table for standards.
 *
 * Design:
 * - Catalog rows pre-populated from standardsCatalog
 * - Yes/No toggle button pair per row
 * - Notes field (inline, collapsed until Yes)
 * - Custom standard entry at bottom
 */
import { useState } from 'react'
import type { StandardRow } from '../../types'

interface Props {
  rows: StandardRow[]
  onToggle: (index: number) => void
  onUpdateNotes: (index: number, notes: string) => void
  onAddCustom: (name: string) => void
  onRemove: (index: number) => void
}

export default function StandardsEditor({ rows, onToggle, onUpdateNotes, onAddCustom, onRemove }: Props) {
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
            <th className="standards-table__col-applies">Applies?</th>
            <th className="standards-table__col-notes">Notes</th>
            <th className="standards-table__col-del" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={`standards-table__row ${row.applies ? 'standards-table__row--yes' : ''}`}>
              <td className="standards-table__name">
                {row.standard_name}
                {row.catalog_id && (
                  <span className="standards-table__catalog-id">{row.catalog_id}</span>
                )}
              </td>
              <td className="standards-table__applies">
                <div className="yes-no-toggle">
                  <button
                    className={`yes-no-toggle__btn ${row.applies ? 'yes-no-toggle__btn--yes' : ''}`}
                    onClick={() => !row.applies && onToggle(i)}
                    aria-pressed={row.applies}
                  >
                    Yes
                  </button>
                  <button
                    className={`yes-no-toggle__btn ${!row.applies ? 'yes-no-toggle__btn--no' : ''}`}
                    onClick={() => row.applies && onToggle(i)}
                    aria-pressed={!row.applies}
                  >
                    No
                  </button>
                </div>
              </td>
              <td className="standards-table__notes">
                {row.applies ? (
                  <input
                    className="standards-table__notes-input"
                    value={row.notes}
                    onChange={e => onUpdateNotes(i, e.target.value)}
                    placeholder="Version, applicability notes…"
                    aria-label={`Notes for ${row.standard_name}`}
                  />
                ) : (
                  <span className="standards-table__notes-na">—</span>
                )}
              </td>
              <td>
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
          ))}
        </tbody>
      </table>

      <div className="standards-editor__add-custom">
        <input
          className="standards-editor__custom-input"
          value={customInput}
          onChange={e => setCustomInput(e.target.value)}
          placeholder="Add custom standard (e.g., MIL-STD-810)"
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

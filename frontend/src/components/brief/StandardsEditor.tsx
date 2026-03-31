/**
 * StandardsEditor — per-module standards multi-select.
 *
 * Each row = one Candidate Module (from Q8).
 * For each module, the user picks one or more standards from a dropdown.
 * "Other" opens a text field that adds a new option dynamically.
 */
import { useState } from 'react'
import type { StandardRow, StandardOption, ModuleRow } from '../../types'
import { PREDEFINED_STANDARDS } from '../../types'

interface Props {
  rows: StandardRow[]
  modules: ModuleRow[]
  onSetModuleStandards: (
    moduleName: string,
    standards: { name: string; catalog_id: string | null }[],
  ) => void
}

export default function StandardsEditor({ rows, modules, onSetModuleStandards }: Props) {
  // Extra standards added via "Other" — shared across all rows so once added it appears for all
  const [customOptions, setCustomOptions] = useState<StandardOption[]>([])
  // Per-module "Other" input visibility and value
  const [otherInput, setOtherInput] = useState<Record<string, string>>({})

  const allOptions: StandardOption[] = [...PREDEFINED_STANDARDS, ...customOptions]

  function getModuleStandards(moduleName: string): StandardOption[] {
    return rows
      .filter(r => r.module_name === moduleName)
      .map(r => ({ name: r.standard_name, catalog_id: r.catalog_id ?? null }))
  }

  function handleSelect(moduleName: string, selectedName: string) {
    if (selectedName === '__other__') {
      setOtherInput(prev => ({ ...prev, [moduleName]: '' }))
      return
    }
    const current = getModuleStandards(moduleName)
    if (current.some(s => s.name === selectedName)) return // already added
    const opt = allOptions.find(o => o.name === selectedName)
    onSetModuleStandards(moduleName, [
      ...current,
      { name: selectedName, catalog_id: opt?.catalog_id ?? null },
    ])
  }

  function handleRemove(moduleName: string, standardName: string) {
    const current = getModuleStandards(moduleName)
    onSetModuleStandards(moduleName, current.filter(s => s.name !== standardName))
  }

  function handleAddOther(moduleName: string) {
    const name = (otherInput[moduleName] ?? '').trim()
    if (!name) return
    // Add to global options if not already present
    if (!allOptions.some(o => o.name === name)) {
      setCustomOptions(prev => [...prev, { name, catalog_id: null }])
    }
    const current = getModuleStandards(moduleName)
    if (!current.some(s => s.name === name)) {
      onSetModuleStandards(moduleName, [...current, { name, catalog_id: null }])
    }
    setOtherInput(prev => { const n = { ...prev }; delete n[moduleName]; return n })
  }

  const namedModules = modules.filter(m => m.name.trim())

  if (!namedModules.length) {
    return (
      <p className="standards-editor__empty">
        Add modules in Candidate Modules first.
      </p>
    )
  }

  return (
    <div className="standards-editor">
      <table className="standards-table">
        <thead>
          <tr>
            <th className="standards-table__col-module">Module</th>
            <th className="standards-table__col-standards">Applied Standards / Architectures</th>
          </tr>
        </thead>
        <tbody>
          {namedModules.map(mod => {
            const selected = getModuleStandards(mod.name)
            const available = allOptions.filter(o => !selected.some(s => s.name === o.name))
            const showingOther = mod.name in otherInput

            return (
              <tr key={mod.name} className="standards-table__row">
                <td className="standards-table__module-name">{mod.name}</td>
                <td className="standards-table__standards-cell">
                  <div className="standards-tags">
                    {selected.map(s => (
                      <span key={s.name} className="standards-tag">
                        {s.name}
                        <button
                          className="standards-tag__remove"
                          onClick={() => handleRemove(mod.name, s.name)}
                          aria-label={`Remove ${s.name} from ${mod.name}`}
                          title="Remove"
                        >
                          ×
                        </button>
                      </span>
                    ))}

                    {showingOther ? (
                      <span className="standards-other-input">
                        <input
                          autoFocus
                          className="standards-other-input__field"
                          value={otherInput[mod.name] ?? ''}
                          onChange={e => setOtherInput(prev => ({ ...prev, [mod.name]: e.target.value }))}
                          placeholder="Standard name…"
                          onKeyDown={e => {
                            if (e.key === 'Enter') handleAddOther(mod.name)
                            if (e.key === 'Escape') setOtherInput(prev => { const n = { ...prev }; delete n[mod.name]; return n })
                          }}
                        />
                        <button
                          className="btn btn--secondary btn--xs"
                          onClick={() => handleAddOther(mod.name)}
                          disabled={!(otherInput[mod.name] ?? '').trim()}
                        >
                          Add
                        </button>
                        <button
                          className="standards-tag__remove"
                          onClick={() => setOtherInput(prev => { const n = { ...prev }; delete n[mod.name]; return n })}
                          title="Cancel"
                        >
                          ×
                        </button>
                      </span>
                    ) : (
                      <select
                        className="standards-add-select"
                        value=""
                        onChange={e => handleSelect(mod.name, e.target.value)}
                        aria-label={`Add standard to ${mod.name}`}
                      >
                        <option value="" disabled>+ Add standard…</option>
                        {available.map(o => (
                          <option key={o.name} value={o.name}>{o.name}</option>
                        ))}
                        <option value="__other__">Other…</option>
                      </select>
                    )}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

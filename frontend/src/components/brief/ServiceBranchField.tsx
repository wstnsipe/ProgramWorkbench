import type { ServiceBranch } from '../../types'

interface Props {
  value: ServiceBranch | null
  armyPae: string | null
  onChange: (branch: ServiceBranch | null, pae?: string | null) => void
  disabled?: boolean
}

const BRANCHES: { value: ServiceBranch; label: string; mig: string }[] = [
  { value: 'USN',  label: 'Navy',        mig: 'MIG-USN-2022'  },
  { value: 'USAF', label: 'Air Force',   mig: 'MIG-USAF-2021' },
  { value: 'USSF', label: 'Space Force', mig: 'MIG-USSF-2023' },
  { value: 'ARMY', label: 'Army',        mig: 'MIG-ARMY-2022' },
]

const ARMY_PAE_OPTIONS = [
  { value: 'PAE_FIRES',    label: 'PAE Fires'   },
  { value: 'PAE_AIR',      label: 'PAE Air'     },
  { value: 'PAE_MANEUVER', label: 'PAE Maneuver' },
]

export default function ServiceBranchField({ value, armyPae, onChange, disabled }: Props) {
  return (
    <div className="service-branch-field">
      <div className="branch-options">
        {BRANCHES.map(b => (
          <label
            key={b.value}
            className={`branch-option ${value === b.value ? 'branch-option--selected' : ''}`}
          >
            <input
              type="radio"
              name="service_branch"
              value={b.value}
              checked={value === b.value}
              onChange={() => onChange(b.value, b.value !== 'ARMY' ? null : armyPae)}
              disabled={disabled}
            />
            <span className="branch-option__label">{b.label}</span>
            <span className="branch-option__mig">{b.mig}</span>
          </label>
        ))}
      </div>

      {value === 'ARMY' && (
        <div className="army-pae-field">
          <label className="field-label" htmlFor="army_pae">
            <span>Army PAE</span>
            <span className="field-label__helper">Portfolio Acquisition Executive</span>
          </label>
          <select
            id="army_pae"
            value={armyPae ?? ''}
            onChange={e => onChange('ARMY', e.target.value || null)}
            disabled={disabled}
          >
            <option value="">— Select PAE —</option>
            {ARMY_PAE_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  )
}

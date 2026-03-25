import type { ServiceBranch, ArmyBranch } from '../../types'

interface Props {
  value: ServiceBranch | null
  armyPae: string | null
  armyBranch: ArmyBranch | null
  onChange: (branch: ServiceBranch | null, pae?: string | null, armyBranch?: ArmyBranch | null) => void
  disabled?: boolean
}

const BRANCHES: { value: ServiceBranch; label: string; mig: string }[] = [
  { value: 'USN',  label: 'Navy',        mig: 'MIG-USN-2022'  },
  { value: 'USAF', label: 'Air Force',   mig: 'MIG-USAF-2021' },
  { value: 'USSF', label: 'Space Force', mig: 'MIG-USSF-2023' },
  { value: 'ARMY', label: 'Army',        mig: 'MIG-ARMY-2022' },
]

const ARMY_PAE_OPTIONS = [
  { value: 'PM_PEO_C3T',    label: 'PM PEO C3T' },
  { value: 'PM_PEO_IEW_S',  label: 'PM PEO IEW&S' },
  { value: 'PM_PEO_CS_CSS', label: 'PM PEO CS&CSS' },
  { value: 'OTHER',         label: 'Other Army' },
]

const ARMY_BRANCH_OPTIONS: { value: ArmyBranch; label: string }[] = [
  { value: 'FIRES',    label: 'Fires' },
  { value: 'MANEUVER', label: 'Maneuver' },
  { value: 'AVIATION', label: 'Aviation' },
]

export default function ServiceBranchField({ value, armyPae, armyBranch, onChange, disabled }: Props) {
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
              onChange={() => onChange(b.value, b.value !== 'ARMY' ? null : armyPae, b.value !== 'ARMY' ? null : armyBranch)}
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
            <span>Army PAE (Program Executive Office)</span>
            <span className="field-label__helper">Selects MIG sub-variant</span>
          </label>
          <select
            id="army_pae"
            value={armyPae ?? ''}
            onChange={e => onChange('ARMY', e.target.value || null, armyBranch)}
            disabled={disabled}
          >
            <option value="">— Select PAE —</option>
            {ARMY_PAE_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <label className="field-label" htmlFor="army_branch" style={{ marginTop: '0.75rem' }}>
            <span>Army Branch</span>
            <span className="field-label__helper">Acquisition community</span>
          </label>
          <select
            id="army_branch"
            value={armyBranch ?? ''}
            onChange={e => onChange('ARMY', armyPae, (e.target.value as ArmyBranch) || null)}
            disabled={disabled}
          >
            <option value="">— Select Branch —</option>
            {ARMY_BRANCH_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  )
}

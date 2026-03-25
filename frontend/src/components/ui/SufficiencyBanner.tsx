import type { SufficiencyResult, SufficiencyLevel } from '../../types'
import Button from '../Button'

interface Props {
  result: SufficiencyResult | null
  loading: boolean
  onRefresh: () => void
}

const LEVEL_CONFIG: Record<SufficiencyLevel, {
  label: string
  cls: string
  icon: string
}> = {
  GREEN:        { label: 'Ready',        cls: 'suf-banner--green',        icon: '✓' },
  YELLOW_HIGH:  { label: 'Nearly Ready', cls: 'suf-banner--yellow-high',  icon: '◐' },
  YELLOW_LOW:   { label: 'Incomplete',   cls: 'suf-banner--yellow-low',   icon: '◑' },
  RED:          { label: 'Not Ready',    cls: 'suf-banner--red',          icon: '✕' },
}

export default function SufficiencyBanner({ result, loading, onRefresh }: Props) {
  if (!result && !loading) {
    return (
      <div className="suf-banner suf-banner--idle">
        <span className="suf-banner__text">Run readiness check to see document generation status</span>
        <Button variant="ghost" size="sm" onClick={onRefresh}>Check readiness</Button>
      </div>
    )
  }

  if (loading) {
    return <div className="suf-banner suf-banner--loading"><span className="suf-banner__text">Checking readiness…</span></div>
  }

  if (!result) return null

  const cfg = LEVEL_CONFIG[result.level]
  const gatesFailed = result.gates.filter(g => !g.passed)

  return (
    <div className={`suf-banner ${cfg.cls}`}>
      <div className="suf-banner__left">
        <span className="suf-banner__icon" aria-hidden="true">{cfg.icon}</span>
        <span className="suf-banner__level">{cfg.label}</span>
        <span className="suf-banner__score">{result.score.toFixed(0)}% coverage</span>
        {result.mig_id && (
          <span className="suf-banner__mig">{result.mig_id}</span>
        )}
      </div>

      <div className="suf-banner__issues">
        {gatesFailed.map(g => (
          <span key={g.gate_id} className="suf-issue suf-issue--gate">
            {g.message}
          </span>
        ))}
        {result.missing_critical.map(label => (
          <span key={label} className="suf-issue suf-issue--missing">
            Missing: {label}
          </span>
        ))}
        {result.rule_violations
          .filter(v => v.severity === 'WARN')
          .slice(0, 2)
          .map(v => (
            <span key={v.rule_id} className="suf-issue suf-issue--warn">
              {v.message}
            </span>
          ))}
      </div>

      <Button variant="ghost" size="sm" onClick={onRefresh} className="suf-banner__refresh">
        Refresh
      </Button>
    </div>
  )
}

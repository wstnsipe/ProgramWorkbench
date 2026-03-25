import type { EvidenceChunk } from '../../hooks/useEvidence'

interface Warning {
  rule_id: string
  severity: string
  message: string
}

interface EvidencePanelProps {
  onClose: () => void
  loading: boolean
  hasDocs: boolean
  chunks: EvidenceChunk[]
  warnings: Warning[]
  context: string
}

export default function EvidencePanel({
  onClose,
  loading,
  hasDocs,
  chunks,
  warnings,
  context,
}: EvidencePanelProps) {
  const errors   = warnings.filter(w => w.severity === 'ERROR')
  const warns    = warnings.filter(w => w.severity === 'WARN')
  const infos    = warnings.filter(w => w.severity === 'INFO')

  return (
    <aside className="evidence-panel">
      <div className="evidence-panel__header">
        <span className="evidence-panel__title">Evidence &amp; Warnings</span>
        <button className="evidence-panel__close" onClick={onClose} aria-label="Close panel">✕</button>
      </div>

      {/* Warnings block */}
      {warnings.length > 0 && (
        <section className="evidence-section">
          <h4 className="evidence-section__heading">Findings</h4>
          <ul className="evidence-finding-list">
            {errors.map(w => (
              <li key={w.rule_id} className="evidence-finding evidence-finding--error">
                <span className="evidence-finding__badge">Error</span>
                {w.message}
              </li>
            ))}
            {warns.map(w => (
              <li key={w.rule_id} className="evidence-finding evidence-finding--warn">
                <span className="evidence-finding__badge">Warn</span>
                {w.message}
              </li>
            ))}
            {infos.map(w => (
              <li key={w.rule_id} className="evidence-finding evidence-finding--info">
                <span className="evidence-finding__badge">Info</span>
                {w.message}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Evidence chunks */}
      <section className="evidence-section">
        <h4 className="evidence-section__heading">
          Relevant Evidence
          <span className="evidence-section__ctx"> — {context}</span>
        </h4>

        {loading && <p className="evidence-empty">Loading…</p>}

        {!loading && !hasDocs && (
          <p className="evidence-empty">No uploaded documents indexed yet.</p>
        )}

        {!loading && hasDocs && chunks.length === 0 && (
          <p className="evidence-empty">No relevant excerpts found for this section.</p>
        )}

        {!loading && chunks.map((c, i) => (
          <div key={i} className="evidence-chunk">
            <div className="evidence-chunk__source">{c.source_filename}</div>
            <p className="evidence-chunk__text">{c.text}{c.text.length >= 300 ? '…' : ''}</p>
          </div>
        ))}
      </section>
    </aside>
  )
}

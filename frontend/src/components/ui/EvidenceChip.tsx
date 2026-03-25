/**
 * EvidenceChip — shows a source file citation inline with generated content.
 * Used in document preview and sufficiency detail views.
 */
interface Props {
  fileId: number
  filename: string
  excerpt?: string
  onClick?: () => void
}

export default function EvidenceChip({ fileId, filename, excerpt, onClick }: Props) {
  return (
    <span
      className={`evidence-chip ${onClick ? 'evidence-chip--clickable' : ''}`}
      title={excerpt ?? filename}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? e => e.key === 'Enter' && onClick() : undefined}
    >
      <span className="evidence-chip__icon" aria-hidden="true">📄</span>
      <span className="evidence-chip__name">
        {filename.length > 28 ? filename.slice(0, 25) + '…' : filename}
      </span>
      <span className="evidence-chip__id">#{fileId}</span>
    </span>
  )
}

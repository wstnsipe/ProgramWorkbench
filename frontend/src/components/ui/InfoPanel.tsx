import type { ReactNode } from 'react'

type Variant = 'info' | 'warning' | 'error' | 'success' | 'tip'

interface Props {
  variant?: Variant
  title?: string
  children: ReactNode
}

const ICONS: Record<Variant, string> = {
  info:    'ℹ',
  warning: '⚠',
  error:   '✕',
  success: '✓',
  tip:     '💡',
}

export default function InfoPanel({ variant = 'info', title, children }: Props) {
  return (
    <div className={`info-panel info-panel--${variant}`} role="note">
      <span className="info-panel__icon" aria-hidden="true">{ICONS[variant]}</span>
      <div className="info-panel__body">
        {title && <strong className="info-panel__title">{title}</strong>}
        <div className="info-panel__text">{children}</div>
      </div>
    </div>
  )
}

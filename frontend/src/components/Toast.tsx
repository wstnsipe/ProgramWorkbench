import { useEffect } from 'react'

interface Props {
  kind: 'success' | 'error' | 'info'
  message: string
  onDismiss: () => void
}

export default function Toast({ kind, message, onDismiss }: Props) {
  useEffect(() => {
    if (kind !== 'error') {
      const t = setTimeout(onDismiss, 4500)
      return () => clearTimeout(t)
    }
  }, [kind, message, onDismiss])

  return (
    <div className={`toast toast--${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <span className="toast-icon" aria-hidden="true">
        {kind === 'success' && '✓'}
        {kind === 'error' && '!'}
        {kind === 'info' && 'i'}
      </span>
      <span className="toast-msg">{message}</span>
      <button className="toast-close" onClick={onDismiss} aria-label="Dismiss">
        ✕
      </button>
    </div>
  )
}

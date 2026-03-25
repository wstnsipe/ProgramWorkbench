/**
 * SaveBar — sticky footer row with Save button + status feedback.
 * Drop into any tab that needs save actions.
 */
import type { SaveStatus } from '../../types'
import Button from '../Button'

interface Props {
  status: SaveStatus
  lastSaved?: Date | null
  onSave: () => void
  disabled?: boolean
  /** Optional extra content (e.g., a Delete button) */
  extra?: React.ReactNode
}

const STATUS_TEXT: Record<SaveStatus, string | null> = {
  idle:   null,
  saving: 'Saving…',
  saved:  'Saved',
  error:  'Save failed',
}

export default function SaveBar({ status, lastSaved, onSave, disabled, extra }: Props) {
  const statusText = STATUS_TEXT[status]

  return (
    <div className="save-bar">
      {extra}
      <div className="save-bar__right">
        {statusText && (
          <span className={`save-bar__status save-bar__status--${status}`}>
            {statusText}
          </span>
        )}
        {status === 'saved' && lastSaved && (
          <span className="save-bar__time">
            {lastSaved.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
        <Button
          onClick={onSave}
          loading={status === 'saving'}
          disabled={disabled || status === 'saving'}
        >
          Save
        </Button>
      </div>
    </div>
  )
}

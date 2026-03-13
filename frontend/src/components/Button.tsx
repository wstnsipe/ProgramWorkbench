import { type ReactNode, type ButtonHTMLAttributes } from 'react'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md'
  loading?: boolean
  children: ReactNode
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  ...rest
}: Props) {
  const cls = [
    'btn',
    `btn--${variant}`,
    size === 'sm' ? 'btn--sm' : '',
    loading ? 'btn--loading' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button className={cls} disabled={disabled || loading} {...rest}>
      {loading && <span className="btn-spin" aria-hidden="true" />}
      {children}
    </button>
  )
}

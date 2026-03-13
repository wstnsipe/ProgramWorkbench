import { type ReactNode } from 'react'

type Variant = 'smart' | 'legacy' | 'success' | 'warning' | 'error' | 'info' | 'default'

interface Props {
  variant?: Variant
  children: ReactNode
}

export default function Badge({ variant = 'default', children }: Props) {
  return <span className={`badge badge--${variant}`}>{children}</span>
}

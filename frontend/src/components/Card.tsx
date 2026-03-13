import { type ReactNode } from 'react'

interface Props {
  children: ReactNode
  className?: string
  noPad?: boolean
}

export default function Card({ children, className = '', noPad = false }: Props) {
  return (
    <div className={`card${noPad ? ' card--no-pad' : ''} ${className}`.trim()}>
      {children}
    </div>
  )
}

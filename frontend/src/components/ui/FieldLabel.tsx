import type { ReactNode } from 'react'

interface Props {
  htmlFor?: string
  required?: boolean
  helper?: string
  children: ReactNode
}

export default function FieldLabel({ htmlFor, required, helper, children }: Props) {
  return (
    <label className="field-label" htmlFor={htmlFor}>
      <span className="field-label__text">
        {children}
        {required && <span className="field-label__req" aria-hidden="true">*</span>}
      </span>
      {helper && <span className="field-label__helper">{helper}</span>}
    </label>
  )
}

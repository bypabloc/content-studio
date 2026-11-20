import { cn } from 'cn'
import type { ReactNode } from 'react'

import { Field, FieldDescription, FieldError, FieldLabel } from '../../shadcn/field'

import { UIIcon } from '../UIIcon'

type Props = {
  label: string
  htmlFor: string
  /** Solo para lectores de pantalla: el texto visible se oculta y sigue siendo el nombre del control. */
  hideLabel?: boolean
  error?: string
  errorId?: string
  /** Pista que va después del error. */
  hint?: ReactNode
  hintId?: string
  className?: string
  children: ReactNode
}

/**
 * Marco de un campo: label visible asociado al control (`htmlFor`), el control (`children`), el error
 * con su ícono (anunciado por `errorId`) y una pista opcional tras el error. Los controles de las
 * moléculas lo usan en vez de repetir Field, FieldLabel y FieldError (spec 008, ciclo 3: REFACTOR).
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIFieldFrame({ label, htmlFor, hideLabel = false, error, errorId, hint, hintId, className, children }: Props): React.JSX.Element {
  return (
    <Field className={cn('gap-1.5', className)}>
      <FieldLabel htmlFor={htmlFor} className={cn('ui-typography-caption font-bold text-foreground-secondary', hideLabel && 'sr-only')}>
        {label}
      </FieldLabel>
      {children}
      {error ? (
        <FieldError id={errorId} className="ui-typography-caption flex items-center gap-1.5 font-bold motion-safe:animate-ui-enter">
          <UIIcon name="circle-alert" className="size-4" />
          {error}
        </FieldError>
      ) : null}
      {hint ? (
        <FieldDescription id={hintId} className="ui-typography-caption">
          {hint}
        </FieldDescription>
      ) : null}
    </Field>
  )
}

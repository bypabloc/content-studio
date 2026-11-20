import { cn } from 'cn'
import { type ComponentProps, type ReactNode, useId } from 'react'

import { Field, FieldDescription, FieldLabel } from '../../shadcn/field'
import { Input } from '../../shadcn/input'

import { UIFieldError } from '../../atoms/UIFieldError'
import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'
import { UIText } from '../../atoms/UIText'

type Props = ComponentProps<'input'> & {
  label: string
  error?: string
  hint?: ReactNode
  icon?: IconName
  endSlot?: ReactNode
  /** Oculta el label visible; el input conserva su nombre accesible para lectores de pantalla. */
  hideLabel?: boolean
  /** Unidad de un campo numérico (`lpm`, `dB HL`): se ve junto al valor y describe el campo. */
  unit?: string
}

const NO_SPINNER = '[appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none'

/**
 * Rango de un campo numérico, con su unidad (`20–250 lpm`), que se muestra junto
 * al error. Si el error ya nombra el máximo (el server lo escribió), no se repite.
 */
function rangeOf(min: Props['min'], max: Props['max'], unit: string | undefined, error: string | undefined): string | null {
  if (min === undefined || max === undefined || !error || error.includes(String(max))) return null
  return unit ? `${min}–${max} ${unit}` : `${min}–${max}`
}

/**
 * Campo de formulario: label visible asociado, ícono inicial opcional, slot
 * final (p. ej. mostrar contraseña), error anunciado y ayuda contextual.
 * Borde de campo con contraste >= 3:1 y anillo de foco de marca. Se arma
 * sobre `Field`, `FieldLabel`, `Input`, `FieldError` y `FieldDescription` de shadcn.
 * Un campo `type="number"` no muestra las flechas nativas y, con `min` y `max`,
 * su error dice el rango (con la `unit`, que se ve dentro del campo).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIField({ label, error, hint, icon, endSlot, hideLabel = false, unit, id, className, ...props }: Props): React.JSX.Element {
  const generated = useId()
  const inputId = id ?? generated
  const errorId = `${inputId}-error`
  const hintId = `${inputId}-hint`
  const unitId = `${inputId}-unit`
  const numeric = props.type === 'number'
  const range = numeric ? rangeOf(props.min, props.max, unit, error) : null
  const rangeId = `${inputId}-range`
  const describedBy = [error ? errorId : null, error && range ? rangeId : null, unit ? unitId : null, hint ? hintId : null].filter(Boolean).join(' ') || undefined
  return (
    <Field className="gap-1.5">
      <FieldLabel htmlFor={inputId} className={cn('ui-typography-caption font-bold text-foreground-secondary', hideLabel && 'sr-only')}>
        {label}
      </FieldLabel>
      <UIBox className="relative">
        {icon ? (
          <UIBox as="span" className={cn('pointer-events-none absolute inset-y-0 left-3.5 flex items-center', error ? 'text-destructive' : 'text-muted-foreground')}>
            <UIIcon name={icon} />
          </UIBox>
        ) : null}
        <Input
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cn(
            'ui-typography-body h-auto rounded-xl bg-card px-3.5 text-base text-foreground transition-[border-color,box-shadow] duration-200',
            'hover:border-foreground-secondary focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 motion-reduce:transition-none md:text-base dark:bg-card',
            hideLabel ? 'min-h-11' : 'min-h-12',
            icon && 'pl-11',
            endSlot && 'pr-12',
            unit && 'pr-16',
            numeric && NO_SPINNER,
            error ? 'border-destructive focus-visible:border-destructive focus-visible:ring-destructive/20' : 'border-input',
            className,
          )}
          {...props}
        />
        {endSlot ? <UIBox as="span" className="absolute inset-y-0 right-1 flex items-center">{endSlot}</UIBox> : null}
        {unit ? (
          <UIBox as="span" id={unitId} className="ui-typography-caption pointer-events-none absolute inset-y-0 right-3.5 flex items-center text-muted-foreground">
            {unit}
          </UIBox>
        ) : null}
      </UIBox>
      {error ? <UIFieldError id={errorId}>{error}</UIFieldError> : null}
      {error && range ? (
        <UIText id={rangeId} className="ui-typography-caption text-foreground-secondary">
          {range}
        </UIText>
      ) : null}
      {hint ? (
        <FieldDescription id={hintId} className="ui-typography-caption">
          {hint}
        </FieldDescription>
      ) : null}
    </Field>
  )
}

import { cn } from 'cn'
import { useId } from 'react'

type Props = {
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  name?: string
  error?: string
  /** Estado parcial (casilla de grupo con algunas opciones marcadas). */
  indeterminate?: boolean
}

/**
 * Casilla única como tarjeta de 44 px nombrada por su label, con
 * descripción opcional (p. ej. el motivo cuando está deshabilitada), foco
 * visible y estado deshabilitado. Con `error`, la casilla queda `aria-invalid`
 * (el formulario la enfoca al enviar) y el texto la describe. Al pulsar la
 * tarjeta se reduce a 0,98 con `motion-safe`, salvo deshabilitada. Con `indeterminate`
 * la casilla muestra el estado parcial del grupo (el DOM lo expone como `indeterminate`).
 *
 * @author Pablo Contreras
 * @since 2026/10/01
 */
export function UICheckbox({ label, description, checked, onChange, disabled, name, error, indeterminate = false }: Props): React.JSX.Element {
  const id = useId()
  const describedBy = [description && `${id}-desc`, error && `${id}-error`].filter(Boolean).join(' ') || undefined
  return (
    <span className="flex flex-col gap-1">
    <label
      htmlFor={id}
      className={cn(
        'flex min-h-11 items-start gap-2.5 rounded-xl border bg-card px-3.5 py-3 has-[:focus-visible]:ui-focus',
        disabled ? 'cursor-not-allowed border-border opacity-70' : 'cursor-pointer border-input hover:border-foreground-secondary',
        checked && !disabled && 'border-primary bg-accent',
        error && 'border-destructive',
        !disabled && 'ui-press',
      )}
    >
      <input
        id={id}
        type="checkbox"
        name={name}
        ref={(element) => {
          if (element) element.indeterminate = indeterminate
        }}
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        aria-labelledby={`${id}-label`}
        aria-describedby={describedBy}
        aria-invalid={error ? true : undefined}
        className={cn(
          'relative mt-0.5 size-5 shrink-0 cursor-pointer appearance-none rounded-md border border-input bg-background checked:border-primary checked:bg-primary indeterminate:border-primary indeterminate:bg-primary',
          'after:absolute after:top-[2px] after:left-[6px] after:h-[9px] after:w-[5px] after:rotate-45 after:border-r-2 after:border-b-2 after:border-primary-foreground after:opacity-0 checked:after:opacity-100 disabled:cursor-not-allowed disabled:opacity-50',
        )}
      />
      <span className="flex flex-col gap-0.5">
        <span id={`${id}-label`} className="ui-typography-body font-bold text-foreground">
          {label}
        </span>
        {description ? (
          <span id={`${id}-desc`} className="ui-typography-caption text-foreground-secondary">
            {description}
          </span>
        ) : null}
      </span>
    </label>
    {error ? (
      <span id={`${id}-error`} className="ui-typography-caption text-destructive">
        {error}
      </span>
    ) : null}
    </span>
  )
}

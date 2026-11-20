/**
 * Switch control with a visible label, optional help text and a 44 px target.
 *
 * @author Pablo Contreras
 * @since 2026/10/25
 */

import { Switch } from '@base-ui/react/switch'
import { useId } from 'react'

import { cn } from 'cn'

type Props = {
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  /** `card`: label y ayuda dentro de una caja. `inline`: solo el control, con el label para lectores de pantalla. */
  variant?: 'card' | 'inline'
}

/** Renders an accessible, keyboard-operable Base UI switch. */
export function UISwitch({ label, description, checked, onChange, disabled = false, variant = 'card' }: Props): React.JSX.Element {
  const id = useId()
  const control = (
    <Switch.Root
      checked={checked}
      disabled={disabled}
      onCheckedChange={onChange}
      aria-labelledby={`${id}-label`}
      aria-describedby={description ? `${id}-description` : undefined}
      className={cn(
        'relative inline-flex min-h-11 min-w-12 shrink-0 cursor-pointer items-center rounded-full border border-input bg-input',
        'transition-colors duration-200 hover:brightness-95 active:brightness-90 focus-visible:ui-focus data-checked:border-primary data-checked:bg-primary disabled:cursor-not-allowed disabled:opacity-60 motion-reduce:transition-none',
      )}
    >
      <Switch.Thumb className="pointer-events-none block size-5 translate-x-1 rounded-full bg-card shadow-ui-sm transition-transform duration-200 data-checked:translate-x-6 motion-reduce:transition-none" />
    </Switch.Root>
  )

  if (variant === 'inline') {
    return (
      <>
        <span id={`${id}-label`} className="sr-only">
          {label}
        </span>
        {control}
      </>
    )
  }

  return (
    <div className="flex min-h-11 items-center justify-between gap-3 rounded-xl border border-input bg-card px-3.5 py-3">
      <span className="flex min-w-0 flex-col gap-0.5">
        <span id={`${id}-label`} className="ui-typography-body font-bold text-foreground">
          {label}
        </span>
        {description ? (
          <span id={`${id}-description`} className="ui-typography-caption text-foreground-secondary">
            {description}
          </span>
        ) : null}
      </span>
      {control}
    </div>
  )
}

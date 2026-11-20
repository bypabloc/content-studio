import { cn } from 'cn'
import { useEffect, useId, useRef } from 'react'

import { Label } from '../../shadcn/label'
import { RadioGroup, RadioGroupItem } from '../../shadcn/radio-group'

import { UIFixedValue } from '../../atoms/UIFixedValue'
import { UIBox } from '../../atoms/UIBox'

type Option = { value: string; label: string; description?: string }
type Props = {
  label: string
  name: string
  options: Option[]
  value: string
  onChange: (value: string) => void
  className?: string
}

/**
 * Opciones excluyentes como tarjetas seleccionables: grupo nombrado por su
 * label visible, cada opción con área táctil de 44 px, descripción
 * opcional, foco visible y flechas del teclado (Base UI). Envía `name` con
 * el formulario. Con exactamente 1 opción, autoselecciona y muestra UIFixedValue.
 * Cada tarjeta se reduce al pulsar (`motion-safe`).
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UIRadioGroup({ label, name, options, value, onChange, className }: Props): React.JSX.Element {
  const labelId = useId()
  const singleOption = options.length === 1 ? options[0] : undefined
  const singleValue = singleOption?.value
  const notifiedRef = useRef<string | null>(null)

  useEffect(() => {
    if (options.length === 1 && singleValue !== undefined && value !== singleValue && notifiedRef.current !== singleValue) {
      notifiedRef.current = singleValue
      onChange(singleValue)
    }
  }, [options.length, singleValue, value, onChange])

  if (options.length === 1 && singleOption) {
    return <UIFixedValue label={label} value={singleOption.label} name={name} hiddenValue={singleOption.value} className={className} />
  }

  return (
    <UIBox className="@container/radio flex flex-col gap-1.5">
      <UIBox as="span" id={labelId} className="ui-typography-caption font-bold text-foreground-secondary">
        {label}
      </UIBox>
      <RadioGroup aria-labelledby={labelId} name={name} value={value} onValueChange={(v) => onChange(String(v))} className={cn('grid-cols-1 gap-2 @xs/radio:grid-cols-2 @2xl/radio:grid-cols-4', className)}>
        {options.map((o) => {
          const id = `${labelId}-${o.value}`
          const checked = o.value === value
          return (
            <Label
              key={o.value}
              htmlFor={id}
              className={cn(
                'flex min-h-11 cursor-pointer items-start gap-2.5 rounded-xl border bg-card px-3.5 py-3 hover:border-foreground-secondary has-[:focus-visible]:ui-focus ui-press',
                checked ? 'border-primary bg-accent' : 'border-input',
              )}
            >
              <RadioGroupItem id={id} value={o.value} aria-labelledby={`${id}-label`} aria-describedby={o.description ? `${id}-desc` : undefined} className="mt-0.5 cursor-pointer" />
              <UIBox as="span" className="flex flex-col gap-0.5">
                <UIBox as="span" id={`${id}-label`} className="ui-typography-body font-bold text-foreground">
                  {o.label}
                </UIBox>
                {o.description ? (
                  <UIBox as="span" id={`${id}-desc`} className="ui-typography-caption text-foreground-secondary">
                    {o.description}
                  </UIBox>
                ) : null}
              </UIBox>
            </Label>
          )
        })}
      </RadioGroup>
    </UIBox>
  )
}

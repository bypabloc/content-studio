import { cn } from 'cn'
import { useEffect, useId, useRef } from 'react'

import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '../../shadcn/dropdown-menu'
import { UIFieldFrame } from '../../atoms/UIFieldFrame'

import { UIButton } from '../../atoms/UIButton'
import { UIFixedValue } from '../../atoms/UIFixedValue'
import { UIHiddenInput } from '../../atoms/UIHiddenInput'
import { UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'

type Props = {
  label: string
  name?: string
  options: { value: string; label: string }[]
  value: string[]
  onChange: (value: string[]) => void
  summary: (n: number) => string
  placeholder: string
  error?: string
  className?: string
}

/**
 * Selector múltiple accesible sobre menú desplegable con casillas de verificación.
 * Opción única: con exactamente 1 opción disponible se autoselecciona y muestra como
 * valor fijo no editable (`UIFixedValue`). Con 2 o más opciones despliega el menú
 * para marcar o desmarcar ítems, enviando inputs ocultos con `name` por cada valor.
 *
 * @author Pablo Contreras
 * @since 2026/09/29
 * @since 2026/11/19
 */
export function UICheckboxGroup({
  label,
  name,
  options,
  value,
  onChange,
  summary,
  placeholder,
  error,
  className,
}: Props): React.JSX.Element {
  const triggerId = useId()
  const errorId = `${triggerId}-error`

  const isSingle = options.length === 1
  const singleOption = isSingle ? options[0] : undefined
  const singleValue = singleOption?.value
  const notifiedRef = useRef(false)

  useEffect(() => {
    if (isSingle && singleValue !== undefined && !value.includes(singleValue) && !notifiedRef.current) {
      notifiedRef.current = true
      onChange([singleValue])
    }
  }, [isSingle, singleValue, value, onChange])

  if (isSingle && singleOption) {
    return (
      <UIFixedValue
        label={label}
        value={singleOption.label}
        name={name}
        hiddenValue={singleOption.value}
        className={className}
      />
    )
  }

  const textTrigger = value.length > 0 ? summary(value.length) : placeholder

  return (
    <UIFieldFrame label={label} htmlFor={triggerId} error={error} errorId={errorId}>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <UIButton
              id={triggerId}
              variant="secondary"
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? errorId : undefined}
              className={cn(
                'ui-typography-body min-h-12 w-full justify-between rounded-xl px-3.5 text-base font-normal text-foreground hover:border-foreground-secondary focus-visible:ui-focus',
                error ? 'border-destructive text-destructive' : 'border-input',
                className,
              )}
            />
          }
        >
          <UIBox as="span">{textTrigger}</UIBox>
          <UIIcon name="chevron-down" className="size-4 shrink-0 text-muted-foreground" />
        </DropdownMenuTrigger>
        <DropdownMenuContent className="min-w-48 bg-card text-foreground">
          {options.map((o) => {
            const checked = value.includes(o.value)
            return (
              <DropdownMenuCheckboxItem
                key={o.value}
                checked={checked}
                onCheckedChange={(nextChecked) => {
                  if (nextChecked) {
                    onChange([...value, o.value])
                  } else {
                    onChange(value.filter((v) => v !== o.value))
                  }
                }}
                closeOnClick={false}
                className="ui-typography-body min-h-11 cursor-pointer px-3 text-foreground"
              >
                {o.label}
              </DropdownMenuCheckboxItem>
            )
          })}
        </DropdownMenuContent>
      </DropdownMenu>
      {name
        ? value.map((v) => (
            <UIHiddenInput key={v} name={name} value={v} />
          ))
        : null}
    </UIFieldFrame>
  )
}

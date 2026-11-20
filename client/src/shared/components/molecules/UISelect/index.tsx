import { lazy, Suspense, useEffect, useId, useRef, useState } from 'react'

import { UIFieldFrame } from '../../atoms/UIFieldFrame'

import { UIFixedValue } from '../../atoms/UIFixedValue'
import { UIHiddenInput } from '../../atoms/UIHiddenInput'
import type { SearchSelectOption } from '../UISearchSelect/Picker'
import { UISkeleton } from '../../atoms/UISkeleton'

const Picker = lazy(async () => ({ default: (await import('../UISearchSelect/Picker')).SearchSelectPicker }))

/** Umbral de opciones a partir del cual el combobox permite filtrar por texto tecleado. */
export const FILTER_THRESHOLD = 8

export type UISelectOption = { value: string; label: string; description?: string; disabled?: boolean }

export type UISelectProps = {
  label: string
  options: UISelectOption[]
  emptyOption?: string
  error?: string
  onChange?: (value: string) => void
  name?: string
  value?: string
  defaultValue?: string
  disabled?: boolean
  id?: string
  className?: string
  required?: boolean
  hideLabel?: boolean
}

/**
 * Select con label visible, opciones traducidas y error anunciado junto al
 * campo. Construido sobre el combobox de Base UI / shadcn.
 *
 * - Opción única: con 1 opción y sin emptyOption, autoselecciona y renderiza
 *   como texto fijo UIFixedValue, sin cargar el combobox.
 * - Con emptyOption y 1 opción, muestra la fila vacía y la opción de solo lectura.
 * - De 2 a 8 opciones: combobox con filterable={false} (solo lectura).
 * - Más de 8 opciones: combobox con filtro por texto.
 * - Con 0 opciones: combobox deshabilitado.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UISelect({
  label,
  options,
  emptyOption,
  error,
  onChange,
  name,
  value,
  defaultValue,
  disabled,
  id,
  className,
  required,
  hideLabel,
}: UISelectProps): React.JSX.Element {
  const generatedId = useId()
  const selectId = id ?? generatedId
  const errorId = `${selectId}-error`

  const [internalValue, setInternalValue] = useState<string>(defaultValue ?? '')
  const currentValue = value !== undefined ? value : internalValue

  const singleOption = options.length === 1 ? options[0] : undefined
  const singleValue = singleOption?.value
  const notifiedRef = useRef<string | null>(null)

  useEffect(() => {
    if (options.length === 1 && !emptyOption && onChange && singleValue !== undefined) {
      if (currentValue !== singleValue && notifiedRef.current !== singleValue) {
        notifiedRef.current = singleValue
        onChange(singleValue)
      }
    }
  }, [options.length, emptyOption, onChange, currentValue, singleValue])

  if (options.length === 1 && !emptyOption && singleOption) {
    return (
      <UIFixedValue
        label={label}
        value={singleOption.label}
        name={name}
        hiddenValue={singleOption.value}
        className={className}
        hideLabel={hideLabel}
      />
    )
  }

  const isDisabled = disabled || options.length === 0
  const items: SearchSelectOption[] = emptyOption !== undefined
    ? [{ value: '', label: emptyOption }, ...options]
    : options

  const filterable = options.length > FILTER_THRESHOLD

  const handleChange = (val: string) => {
    if (value === undefined) {
      setInternalValue(val)
    }
    onChange?.(val)
  }

  const handleInputCleared = () => {
    if (emptyOption !== undefined) {
      if (value === undefined) {
        setInternalValue('')
      }
      onChange?.('')
    }
  }

  return (
    <UIFieldFrame label={label} htmlFor={selectId} hideLabel={hideLabel} error={error} errorId={errorId} className={className}>
      {name && !disabled && options.length > 0 ? (
        <UIHiddenInput name={name} value={currentValue} />
      ) : null}
      <Suspense fallback={<UISkeleton className="h-12 w-full rounded-xl" />}>
        <Picker
          id={selectId}
          label={label}
          showLabel={false}
          options={items}
          value={currentValue}
          onChange={handleChange}
          onInputCleared={handleInputCleared}
          empty={emptyOption ?? ''}
          error={error}
          disabled={isDisabled}
          filterable={filterable}
          required={required}
        />
      </Suspense>
    </UIFieldFrame>
  )
}

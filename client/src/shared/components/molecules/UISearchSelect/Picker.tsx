import { cn } from 'cn'
import { useId, useState } from 'react'

import { Combobox, ComboboxContent, ComboboxEmpty, ComboboxInput, ComboboxItem, ComboboxList } from '../../shadcn/combobox'
import { UIFieldFrame } from '../../atoms/UIFieldFrame'

import { UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'

/** Opción del selector: valor, texto visible y descripción opcional. */
export type SearchSelectOption = { value: string; label: string; description?: string; disabled?: boolean }

/** Props de `UISearchSelect`, las mismas del combobox interno. */
export type SearchSelectProps = {
  label: string
  options: SearchSelectOption[]
  value: string
  onChange: (value: string) => void
  empty: string
  placeholder?: string
  error?: string
  id?: string
  showLabel?: boolean
  disabled?: boolean
  filterable?: boolean
  onInputCleared?: () => void
  required?: boolean
  className?: string
}

/**
 * Combobox de `UISearchSelect` y `UISelect` (Base UI): el campo muestra la
 * opción elegida; al escribir filtra por su texto (si `filterable` no es false),
 * las flechas recorren, Enter o clic elige y Escape cierra. Si se sale del campo
 * o se cierra el popup sin elegir, vuelve a mostrar la opción elegida. Vive en su
 * propio módulo para que `UISearchSelect` y `UISelect` lo carguen bajo demanda y
 * las pantallas sin selector no descarguen Base UI.
 *
 * @author Pablo Contreras
 * @since 2026/10/08
 */
export function SearchSelectPicker({
  label,
  options,
  value,
  onChange,
  empty,
  placeholder,
  error,
  id,
  showLabel = true,
  disabled = false,
  filterable = true,
  onInputCleared,
  required,
  className,
}: SearchSelectProps): React.JSX.Element {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const errorId = `${inputId}-error`
  const chosen = options.find((o) => o.value === value) ?? null
  const [open, setOpen] = useState(false)
  // Texto que escribe el usuario; `null` muestra la etiqueta de la opción elegida.
  const [typedText, setTypedText] = useState<string | null>(null)
  const inputValue = typedText ?? chosen?.label ?? ''

  const content = (
    <Combobox<SearchSelectOption>
      items={options}
      value={chosen}
      inputValue={inputValue}
      open={open}
      onOpenChange={(nextOpen, details) => {
        setOpen(nextOpen)
        // Al vaciar el texto Base UI cierra el popup: el texto vacío se conserva mientras se edita.
        if (!nextOpen && details.reason !== 'input-clear') {
          setTypedText(null)
        }
      }}
      onInputValueChange={(text, details) => {
        if (details?.reason === 'escape-key') {
          details.cancel()
          details.allowPropagation()
          return
        }
        const typing = details?.reason === 'input-change' || details?.reason === 'input-clear'
        setTypedText(typing ? text : null)
      }}
      onValueChange={(option, details) => {
        if (details?.reason === 'escape-key') {
          details.cancel()
          details.allowPropagation()
          return
        }
        if (option) {
          setTypedText(null)
          onChange(option.value)
        } else {
          onInputCleared?.()
        }
      }}
      isItemEqualToValue={(a, b) => a.value === b.value}
      autoHighlight
      disabled={disabled}
    >
      <UIBox className="relative">
        {filterable ? (
          <UIBox as="span" className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-muted-foreground">
            <UIIcon name="search" />
          </UIBox>
        ) : null}
        <ComboboxInput
          id={inputId}
          aria-label={!showLabel ? label : undefined}
          placeholder={placeholder}
          readOnly={!filterable}
          onBlur={() => setTypedText(null)}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          aria-required={required ? true : undefined}
          className={cn(
            'ui-typography-body h-auto min-h-12 cursor-pointer rounded-xl bg-card pr-11 text-base text-foreground hover:border-foreground-secondary focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 md:text-base dark:bg-card',
            filterable ? 'pl-11' : 'px-3.5',
            chosen?.value === '' && 'text-muted-foreground',
            error ? 'border-destructive' : 'border-input',
            className,
          )}
        />
        <UIBox as="span" className="pointer-events-none absolute inset-y-0 right-3.5 flex items-center text-muted-foreground">
          <UIIcon name="chevron-down" />
        </UIBox>
      </UIBox>
      <ComboboxContent className="bg-card text-foreground shadow-ui-lg">
        {empty ? (
          <ComboboxEmpty className="ui-typography-body min-h-11 items-center px-3 text-muted-foreground">
            {empty}
          </ComboboxEmpty>
        ) : null}
        <ComboboxList>
          {(option: SearchSelectOption) => (
            <ComboboxItem
              key={option.value}
              value={option}
              disabled={option.disabled}
              data-value={option.value}
              className={cn(
                'ui-typography-body min-h-11 cursor-pointer gap-3 px-3 py-2 text-foreground data-highlighted:bg-accent data-highlighted:text-accent-foreground data-selected:font-bold',
                option.value === '' && 'text-muted-foreground',
              )}
            >
              <UIBox as="span" className="flex min-w-0 flex-1 flex-col">
                <UIBox as="span" className="wrap-break-word">{option.label}</UIBox>
                {option.description ? (
                  <UIBox as="span" className="ui-typography-caption wrap-break-word text-muted-foreground">
                    {option.description}
                  </UIBox>
                ) : null}
              </UIBox>
              {option.value === value ? <UIIcon name="check" className="size-4 shrink-0 text-primary" /> : null}
            </ComboboxItem>
          )}
        </ComboboxList>
      </ComboboxContent>
    </Combobox>
  )

  if (!showLabel) {
    return content
  }

  return (
    <UIFieldFrame label={label} htmlFor={inputId} error={error} errorId={errorId}>
      {content}
    </UIFieldFrame>
  )
}

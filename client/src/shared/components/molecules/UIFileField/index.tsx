import { cn } from 'cn'
import {
  type ChangeEvent,
  type ComponentProps,
  type ReactNode,
  useId,
  useState,
} from 'react'

import { FieldDescription } from '../../shadcn/field'
import { Input } from '../../shadcn/input'
import { Label } from '../../shadcn/label'

import { UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'
import { UIFieldFrame } from '../../atoms/UIFieldFrame'

type Props = Omit<ComponentProps<'input'>, 'type' | 'onChange' | 'value'> & {
  label: string
  error?: string
  hint?: ReactNode
  accept?: string
  maxBytes?: number
  maxBytesError: string
  /** Texto del botón que abre el selector (el input nativo muestra el del navegador, en inglés). */
  chooseLabel: string
  /** Texto cuando no hay archivo elegido. */
  emptyLabel: string
  onFile?: (file: File) => void
}

/**
 * Campo de selección de archivo: label visible asociado, tipo file oculto
 * tras un disparador propio en español («Elegir archivo» y el nombre elegido),
 * validación de tamaño en cliente antes de emitir evento, área táctil de 44px
 * y accesibilidad mediante `aria-invalid` y `aria-describedby`.
 *
 * @author Pablo Contreras
 * @since 2026/09/30
 * @since 2026/11/19
 */
export function UIFileField({
  label,
  error,
  hint,
  accept,
  maxBytes,
  maxBytesError,
  chooseLabel,
  emptyLabel,
  onFile,
  id,
  className,
  disabled,
  ...props
}: Props): React.JSX.Element {
  const generated = useId()
  const inputId = id ?? generated
  const errorId = `${inputId}-error`
  const hintId = `${inputId}-hint`
  const [localError, setLocalError] = useState<string | undefined>(undefined)
  const [fileName, setFileName] = useState<string | null>(null)

  const activeError = error ?? localError
  const describedBy =
    [activeError ? errorId : null, hint ? hintId : null]
      .filter(Boolean)
      .join(' ') || undefined

  const handleChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0]
    if (!file) {
      setLocalError(undefined)
      setFileName(null)
      return
    }

    if (maxBytes && file.size > maxBytes) {
      setLocalError(maxBytesError)
      setFileName(null)
      e.target.value = ''
      return
    }

    setLocalError(undefined)
    setFileName(file.name)
    onFile?.(file)
  }

  return (
    <UIFieldFrame label={label} htmlFor={inputId} error={activeError} errorId={errorId}>
      {/* El input nativo queda accesible (foco, etiqueta, setInputFiles) pero oculto: su texto es del navegador. */}
      <Label
        htmlFor={inputId}
        className={cn(
          'ui-typography-body relative flex min-h-11 cursor-pointer flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border bg-card px-1.5 py-1.5 text-foreground transition-[border-color,box-shadow] duration-200 hover:border-foreground-secondary',
          'has-[:focus-visible]:border-ring has-[:focus-visible]:ring-4 has-[:focus-visible]:ring-ring/20 motion-reduce:transition-none',
          activeError ? 'border-destructive has-[:focus-visible]:border-destructive has-[:focus-visible]:ring-destructive/20' : 'border-input',
          disabled && 'cursor-not-allowed opacity-50',
          className,
        )}
      >
        <Input
          id={inputId}
          type="file"
          accept={accept}
          disabled={disabled}
          aria-invalid={activeError ? true : undefined}
          aria-describedby={describedBy}
          onChange={handleChange}
          className="sr-only"
          {...props}
        />
        <UIBox as="span" aria-hidden="true" className="inline-flex min-h-8 shrink-0 items-center gap-2 rounded-lg bg-muted px-3 font-bold text-foreground">
          <UIIcon name="upload" className="size-4" />
          {chooseLabel}
        </UIBox>
        <UIBox as="span" aria-hidden="true" className={cn('min-w-32 flex-1 wrap-break-word', fileName ? 'text-foreground' : 'text-foreground-secondary')}>
          {fileName ?? emptyLabel}
        </UIBox>
      </Label>
      {hint ? (
        <FieldDescription
          id={hintId}
          className="ui-typography-caption text-foreground-secondary"
        >
          {hint}
        </FieldDescription>
      ) : null}
    </UIFieldFrame>
  )
}

import { cn } from 'cn'
import {
  type ChangeEvent,
  type DragEvent,
  type KeyboardEvent,
  type ReactNode,
  useId,
  useRef,
  useState,
} from 'react'

import { Input } from '../../shadcn/input'
import { Label } from '../../shadcn/label'

import { UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'
import { UIText } from '../../atoms/UIText'

/** Motivo por el que la zona descarta un archivo antes de entregarlo. */
export type FileDropRejection = {
  file: File
  reason: 'too_large' | 'type_not_allowed'
}

type Props = {
  label: string
  /** Texto del disparador («Elegir archivos»). */
  chooseLabel: string
  /** Texto que invita a arrastrar («o arrástralos aquí»). */
  dropLabel: string
  hint?: ReactNode
  /** Lista como la de `<input accept>`: tipos MIME, `tipo/*` o extensiones `.ext`. */
  accept?: string
  maxBytes?: number
  disabled?: boolean
  id?: string
  className?: string
  /** Recibe los archivos aceptados y los descartados con su motivo. */
  onFiles: (accepted: File[], rejected: FileDropRejection[]) => void
}

/**
 * Indica si un archivo cumple la lista `accept` (MIME exacto, `tipo/*` o extensión).
 *
 * @author Pablo Contreras
 * @since 2026/11/05
 */
export function matchesAccept(file: File, accept: string | undefined): boolean {
  if (!accept) return true
  const name = file.name.toLowerCase()
  return accept.split(',').some((raw) => {
    const token = raw.trim().toLowerCase()
    if (token.startsWith('.')) return name.endsWith(token)
    if (token.endsWith('/*')) return file.type.startsWith(token.slice(0, -1))
    return file.type === token
  })
}

/**
 * Zona para arrastrar o elegir varios archivos: se abre con clic, Enter o
 * Espacio, se resalta al arrastrar (`data-dragging`) y separa los archivos
 * aceptados de los que superan `maxBytes` o no cumplen `accept`.
 *
 * @author Pablo Contreras
 * @since 2026/11/05
 */
export function UIFileDrop({
  label,
  chooseLabel,
  dropLabel,
  hint,
  accept,
  maxBytes,
  disabled,
  id,
  className,
  onFiles,
}: Props): React.JSX.Element {
  const generated = useId()
  const inputId = id ?? generated
  const hintId = `${inputId}-hint`
  const input = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const deliver = (files: File[]): void => {
    if (disabled || files.length === 0) return
    const accepted: File[] = []
    const rejected: FileDropRejection[] = []
    for (const file of files) {
      if (maxBytes && file.size > maxBytes) rejected.push({ file, reason: 'too_large' })
      else if (!matchesAccept(file, accept)) rejected.push({ file, reason: 'type_not_allowed' })
      else accepted.push(file)
    }
    onFiles(accepted, rejected)
  }

  const open = (): void => {
    if (!disabled) input.current?.click()
  }

  const handleKey = (e: KeyboardEvent<HTMLDivElement>): void => {
    if (e.key !== 'Enter' && e.key !== ' ') return
    e.preventDefault()
    open()
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault()
    if (!disabled) setDragging(true)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault()
    setDragging(false)
    deliver(Array.from(e.dataTransfer.files))
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>): void => {
    deliver(Array.from(e.target.files ?? []))
    e.target.value = ''
  }

  return (
    <UIBox className="flex flex-col gap-1.5">
      <Label htmlFor={inputId} className="ui-typography-caption font-bold text-foreground-secondary">
        {label}
      </Label>
      <Input
        ref={input}
        id={inputId}
        type="file"
        multiple
        accept={accept}
        disabled={disabled}
        tabIndex={-1}
        onChange={handleChange}
        className="sr-only"
      />
      <UIBox
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled ? true : undefined}
        aria-describedby={hint ? hintId : undefined}
        data-dragging={dragging ? 'true' : undefined}
        onClick={open}
        onKeyDown={handleKey}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={cn(
          'ui-typography-body flex min-h-24 cursor-pointer flex-col items-center justify-center gap-2 rounded-xl',
          'border-2 border-dashed border-input bg-card px-4 py-5 text-center text-foreground',
          'transition-[border-color,background-color,box-shadow] duration-200 motion-reduce:transition-none',
          'hover:border-foreground-secondary focus-visible:border-ring focus-visible:outline-none',
          'focus-visible:ring-4 focus-visible:ring-ring/20 data-[dragging=true]:border-primary data-[dragging=true]:bg-primary/5',
          disabled && 'cursor-not-allowed opacity-50',
          className,
        )}
      >
        <UIBox as="span" className="inline-flex min-h-9 items-center gap-2 rounded-lg bg-muted px-3 font-bold">
          <UIIcon name="upload" className="size-4" />
          {chooseLabel}
        </UIBox>
        <UIBox as="span" className="text-foreground-secondary">{dropLabel}</UIBox>
      </UIBox>
      {hint ? (
        <UIText id={hintId} className="ui-typography-caption text-foreground-secondary">
          {hint}
        </UIText>
      ) : null}
    </UIBox>
  )
}

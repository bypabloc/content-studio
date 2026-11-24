import { cn } from 'cn'
import { type ComponentProps, type ReactNode, useId } from 'react'

import { UIFieldFrame } from '../../atoms/UIFieldFrame'
import { Textarea } from '../../shadcn/textarea'


type Props = ComponentProps<'textarea'> & { label: string; error?: string; hint?: ReactNode; hideLabel?: boolean }

/**
 * Área de texto con label visible asociado, error anunciado junto al campo
 * y ayuda contextual; mismos tokens, borde y foco que `UIField`. Con
 * `hideLabel` la etiqueta queda solo para lectores de pantalla, como en `UIField`.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UITextarea({ label, error, hint, hideLabel = false, id, className, ...props }: Props): React.JSX.Element {
  const generated = useId()
  const areaId = id ?? generated
  const errorId = `${areaId}-error`
  const hintId = `${areaId}-hint`
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ') || undefined
  return (
    <UIFieldFrame label={label} htmlFor={areaId} hideLabel={hideLabel} error={error} errorId={errorId} hint={hint} hintId={hintId}>
      <Textarea
        id={areaId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          'ui-typography-body min-h-24 resize-none rounded-xl bg-card px-3.5 py-3 text-base text-foreground transition-[border-color,box-shadow] duration-200 hover:border-foreground-secondary',
          'focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 motion-reduce:transition-none md:text-base dark:bg-card',
          error ? 'border-destructive focus-visible:border-destructive focus-visible:ring-destructive/20' : 'border-input',
          className,
        )}
        {...props}
      />
    </UIFieldFrame>
  )
}

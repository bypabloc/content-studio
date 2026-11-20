import { cn } from 'cn'

import { FieldError } from '../../shadcn/field'

import { UIIcon } from '../UIIcon'

/**
 * Error de un campo o de una pregunta sin campo propio: se anuncia como alerta
 * y lleva un ícono junto al texto, para que el error no dependa solo del color.
 * Lo usan `UIField` y las preguntas de la encuesta (radios, escalas, grupos).
 *
 * @author Pablo Contreras
 * @since 2026/11/12
 * @since 2026/11/19
 */
export function UIFieldError({
  id,
  className,
  children,
}: {
  id?: string
  className?: string
  children: React.ReactNode
}): React.JSX.Element {
  return (
    <FieldError id={id} className={cn('ui-typography-caption flex items-center gap-1.5 font-bold motion-safe:animate-ui-enter', className)}>
      <UIIcon name="circle-alert" className="size-4" />
      {children}
    </FieldError>
  )
}

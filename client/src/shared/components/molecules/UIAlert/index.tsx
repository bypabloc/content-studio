import { cn } from 'cn'
import type { ReactNode, Ref } from 'react'

import { Alert, AlertDescription } from '../../shadcn/alert'

import { UIIcon } from '../../atoms/UIIcon'

const TONES = {
  danger: { role: 'alert', icon: 'circle-alert', variant: 'destructive', className: 'border-destructive/30 bg-destructive-soft text-destructive' },
  info: { role: 'status', icon: 'circle-check', variant: 'default', className: 'border-primary/25 bg-accent text-accent-foreground' },
} as const

type Props = {
  tone?: keyof typeof TONES
  children: ReactNode
  /** Elemento de la alerta: permite enfocarla (p. ej. un resumen de errores). */
  ref?: Ref<HTMLDivElement>
  tabIndex?: number
  className?: string
}

/**
 * Mensaje destacado con ícono. `danger` interrumpe (`role="alert"`);
 * `info` se anuncia sin interrumpir (`role="status"`). `ref`, `tabIndex` y
 * `className` se aplican al propio elemento de la alerta.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIAlert({ tone = 'danger', children, ref, tabIndex, className: extra }: Props): React.JSX.Element {
  const { role, icon, variant, className } = TONES[tone]
  return (
    <Alert
      ref={ref}
      tabIndex={tabIndex}
      role={role}
      variant={variant}
      className={cn('ui-typography-body items-start gap-x-3 rounded-xl border px-4 py-3 text-base font-bold motion-safe:animate-ui-enter', className, extra)}
    >
      <UIIcon name={icon} className="mt-0.5 size-5" />
      <AlertDescription className="text-base font-bold text-current">{children}</AlertDescription>
    </Alert>
  )
}

import { cn } from 'cn'
import type { ReactNode } from 'react'

import { Badge } from '../../shadcn/badge'
import { type IconName, UIIcon } from '../UIIcon'

const TONES = {
  neutral: 'bg-muted text-foreground-secondary ring-border',
  brand: 'bg-accent text-accent-foreground ring-primary/20',
  accent: 'bg-success-soft text-success ring-success/20',
  danger: 'bg-destructive-soft text-destructive ring-destructive/20',
} as const

type Props = { tone?: keyof typeof TONES; icon?: IconName; children: ReactNode }

/**
 * Etiqueta compacta de estado o categoría.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIBadge({ tone = 'neutral', icon, children }: Props): React.JSX.Element {
  return (
    <Badge variant="secondary" className={cn('ui-typography-caption h-auto rounded-full px-2.5 py-0.5 font-bold ring-1 ring-inset', TONES[tone])}>
      {icon && <UIIcon name={icon} className="size-3.5" />}
      {children}
    </Badge>
  )
}

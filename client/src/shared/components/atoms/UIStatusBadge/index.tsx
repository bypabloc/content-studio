import { cn } from 'cn'

import { Badge } from '../../shadcn/badge'

import { type IconName, UIIcon } from '../UIIcon'

/** Status of a laboratory order. */
export type LabOrderStatus = 'pending' | 'sent' | 'received' | 'delivered' | 'voided'

const STYLES: Record<LabOrderStatus, { tone: string; icon: IconName }> = {
  pending: { tone: 'bg-muted text-foreground-secondary ring-border', icon: 'clock' },
  sent: { tone: 'bg-accent text-accent-foreground ring-primary/20', icon: 'send' },
  received: { tone: 'bg-accent text-accent-foreground ring-primary', icon: 'package-check' },
  delivered: { tone: 'bg-success-soft text-success ring-success/20', icon: 'circle-check' },
  voided: { tone: 'bg-destructive-soft text-destructive ring-destructive/20', icon: 'ban' },
}

/**
 * Order status badge: text and icon per status (doesn't depend
 * only on color); the text arrives translated.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UIStatusBadge({ status, label }: { status: LabOrderStatus; label: string }): React.JSX.Element {
  const { tone, icon } = STYLES[status]
  return (
    <Badge variant="secondary" data-status={status} className={cn('ui-typography-caption h-auto gap-1 rounded-full px-2.5 py-0.5 font-bold ring-1 ring-inset transition-colors duration-200 motion-reduce:transition-none', tone)}>
      <UIIcon name={icon} className="size-3.5" />
      {label}
    </Badge>
  )
}

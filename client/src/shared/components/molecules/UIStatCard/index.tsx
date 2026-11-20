import { cn } from 'cn'

import { UICard } from '../../atoms/UICard'
import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { UILink } from '../../atoms/UILink'
import { UIBox } from '../../atoms/UIBox'
import { UIText } from '../../atoms/UIText'

type Direction = 'up' | 'down' | 'flat'

type Props = {
  label: string
  value: string
  delta?: { value: string; direction: Direction; label: string; positiveIsGood: boolean }
  description: string
  icon: IconName
  href?: string
  linkLabel?: string
  'data-analytics'?: 'dashboard.card'
  'data-analytics-detail'?: string
}

const DIRECTION_ICON = { up: 'trending-up', down: 'trending-down', flat: 'minus' } as const satisfies Record<Direction, IconName>

const TONES = {
  good: 'bg-success-soft text-success',
  bad: 'bg-destructive-soft text-destructive',
  flat: 'bg-muted text-muted-foreground',
} as const

const toneOf = (direction: Direction, positiveIsGood: boolean): keyof typeof TONES =>
  direction === 'flat' ? 'flat' : (direction === 'up') === positiveIsGood ? 'good' : 'bad'

/**
 * Indicador (KPI): región nombrada por `label` con el valor ya formateado,
 * variación con tono semántico (éxito o alerta según `positiveIsGood`, neutro
 * si no cambia) y dirección anunciada en texto `sr-only`, descripción de qué
 * mide y enlace opcional al detalle.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UIStatCard({ label, value, delta, description, icon, href, linkLabel, 'data-analytics': analyticsId, 'data-analytics-detail': id }: Props): React.JSX.Element {
  const tone = delta ? toneOf(delta.direction, delta.positiveIsGood) : 'flat'
  return (
    <UICard aria-label={label} className="flex flex-col gap-3 p-5 sm:p-6" data-analytics={analyticsId} data-analytics-detail={id}>
      <UIBox className="flex items-start justify-between gap-3">
        <UIText className="ui-typography-caption font-bold text-foreground-secondary">{label}</UIText>
        <UIBox as="span" className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-accent text-accent-foreground">
          <UIIcon name={icon} />
        </UIBox>
      </UIBox>
      <UIText className="ui-typography-title-3 text-foreground tabular-nums wrap-break-word">{value}</UIText>
      {delta ? (
        <UIBox as="span" data-tone={tone} className={cn('ui-typography-caption inline-flex w-fit items-center gap-1 rounded-full px-2 py-0.5 font-bold tabular-nums', TONES[tone])}>
          <UIIcon name={DIRECTION_ICON[delta.direction]} className="size-4" />
          <UIBox as="span" className="sr-only">{delta.label}</UIBox>
          {delta.value}
        </UIBox>
      ) : null}
      <UIText className="ui-typography-caption text-muted-foreground">{description}</UIText>
      {href && linkLabel ? (
        <UILink href={href} className="ui-typography-body inline-flex min-h-11 w-fit items-center gap-1.5 rounded-lg font-bold text-accent-foreground underline-offset-4 hover:underline focus-visible:ui-focus">
          {linkLabel}
          <UIIcon name="arrow-right" className="size-4" />
        </UILink>
      ) : null}
    </UICard>
  )
}

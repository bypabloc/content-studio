import { type ReactNode, useId, useState } from 'react'

import { UIAlert } from '../../molecules/UIAlert'
import { UIButton } from '../../atoms/UIButton'
import { UICard } from '../../atoms/UICard'
import { UIChartPlaceholder } from '../../atoms/UIChartPlaceholder'
import { UICollapsible } from '../../molecules/UICollapsible'
import { UIEmpty } from '../../molecules/UIEmpty'
import { UISkeleton } from '../../atoms/UISkeleton'
import { UIStatus } from '../../atoms/UIStatus'
import { UITable, type UITableColumn } from '../UITable'
import { UIBox } from '../../atoms/UIBox'
import { UIText } from '../../atoms/UIText'

type Column = { key: string; label: string; align?: 'left' | 'right' }
type Row = Record<string, ReactNode>

type Props = {
  title: string
  description: string
  howToRead: string
  state: 'loading' | 'empty' | 'error' | 'ready'
  onRetry?: () => void
  table: { columns: Column[]; rows: Row[] }
  height?: number
  labels: { howToRead: string; showData: string; hideData: string; retry: string; error: string; empty: string; emptyDescription?: string; loading: string }
  children: ReactNode
}

type Indexed = { i: number; row: Row }

/**
 * Tarjeta de gráfica: región nombrada por el título (`h3`), descripción de
 * qué mide, "Cómo leerla" plegable, estados de carga (esqueleto con la altura
 * de la gráfica), vacío y error (con reintentar), y "Ver datos": la misma
 * información como tabla accesible (`UITable`, cifras a la derecha).
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 */
export function UIChartCard({ title, description, howToRead, state, onRetry, table, height = 280, labels, children }: Props): React.JSX.Element {
  const [showData, setShowData] = useState(false)
  const tableId = useId()
  const columns: UITableColumn<Indexed>[] = table.columns.map((c) => ({
    key: c.key,
    header: c.label,
    align: c.align === 'right' ? 'end' : 'start',
    render: ({ row }) => row[c.key],
  }))
  const dataVisible = state === 'ready' && showData

  const body: Record<Props['state'], ReactNode> = {
    loading: (
      <UIStatus label={labels.loading}>
        <UIBox className="relative w-full">
          {/* Reserva la altura de la gráfica: el diseño no salta al cargar (CLS). */}
          <UIChartPlaceholder height={height} />
          <UISkeleton className="absolute inset-0 size-full rounded-xl" />
        </UIBox>
      </UIStatus>
    ),
    empty: <UIEmpty icon="chart-column" title={labels.empty} description={labels.emptyDescription} level={4} />,
    error: (
      <UIBox className="flex flex-col items-start gap-3">
        <UIAlert tone="danger">{labels.error}</UIAlert>
        {onRetry ? (
          <UIButton variant="secondary" icon="refresh-cw" onClick={onRetry}>
            {labels.retry}
          </UIButton>
        ) : null}
      </UIBox>
    ),
    ready: <UIBox className="motion-safe:animate-ui-fade">{children}</UIBox>,
  }

  return (
    <UICard aria-label={title} className="flex min-w-0 flex-col gap-4 p-5 sm:p-6">
      <UIBox className="flex flex-col gap-1">
        <UIBox role="heading" aria-level={3} className="ui-typography-subtitle-2 text-foreground">{title}</UIBox>
        <UIText className="ui-typography-body text-foreground-secondary">{description}</UIText>
      </UIBox>
      <UIBox className="min-w-0">{body[state]}</UIBox>
      <UIBox className="flex flex-col items-start gap-2 sm:flex-row sm:flex-wrap sm:justify-between">
        <UIBox className="min-w-0 flex-1">
          <UICollapsible trigger={labels.howToRead}>{howToRead}</UICollapsible>
        </UIBox>
        {state === 'ready' ? (
          <UIButton variant="ghost" icon="table" className="min-h-11" aria-expanded={showData} aria-controls={dataVisible ? tableId : undefined} onClick={() => setShowData((v) => !v)}>
            {showData ? labels.hideData : labels.showData}
          </UIButton>
        ) : null}
      </UIBox>
      {dataVisible ? (
        <UIBox id={tableId} className="min-w-0 overflow-x-auto">
          <UITable caption={title} columns={columns} rows={table.rows.map((row, i) => ({ i, row }))} rowKey={({ i }) => i} />
        </UIBox>
      ) : null}
    </UICard>
  )
}

import { type ComponentProps, lazy, Suspense } from 'react'

import { UIBox } from '../../atoms/UIBox'
import { UIChartPlaceholder } from '../../atoms/UIChartPlaceholder'
import { UISkeleton } from '../../atoms/UISkeleton'
import type { UIChartBody } from './body'

export { axisWidth } from './axis'
export type { ChartBand, ChartKind, ChartSeries } from './types'

// recharts y shadcn/chart pesan: se cargan al primer uso, fuera del bundle inicial (spec 008).
const Body = lazy(() => import('./body').then((module) => ({ default: module.UIChartBody })))

type Props = ComponentProps<typeof UIChartBody>

/**
 * Gráfica sobre los tokens `--chart-*`. Mientras carga recharts muestra el mismo esqueleto, con la altura final, que
 * `UIChartCard`. La lógica de cada tipo está en `body.tsx`.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UIChart(props: Props): React.JSX.Element {
  return (
    <Suspense
      fallback={
        <UIBox className="relative w-full">
          <UIChartPlaceholder height={props.height ?? 280} />
          <UISkeleton className="absolute inset-0 size-full rounded-xl" />
        </UIBox>
      }
    >
      <Body {...props} />
    </Suspense>
  )
}

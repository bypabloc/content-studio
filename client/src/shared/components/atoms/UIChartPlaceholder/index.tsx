type Props = { height: number }

/**
 * Hueco con la altura de la gráfica (spec 008): reserva el espacio mientras carga recharts, para que el diseño no salte
 * (CLS). Usa el atributo `height` del SVG y no una prop `style`. Lo usan `UIChartCard` y el `Suspense` de `UIChart`.
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIChartPlaceholder({ height }: Props): React.JSX.Element {
  return <svg aria-hidden="true" focusable="false" data-slot="chart-placeholder" className="block w-full" height={height} />
}

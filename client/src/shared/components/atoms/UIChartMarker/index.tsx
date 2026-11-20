type Props = { cx?: number; cy?: number; color: string }

/**
 * Marca en cruz de un punto de la gráfica (spec 008, D-3). Es un `path` dentro del SVG de recharts, así que no puede
 * vivir en un organismo. Sin coordenadas válidas dibuja un `g` vacío.
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIChartMarker({ cx, cy, color }: Props): React.JSX.Element {
  if (cx === undefined || cy === undefined || Number.isNaN(cx) || Number.isNaN(cy)) return <g />
  return <path d={`M${cx - 4},${cy - 4}L${cx + 4},${cy + 4}M${cx - 4},${cy + 4}L${cx + 4},${cy - 4}`} stroke={color} strokeWidth={2} /> // i18n-ignore: geometría del trazo SVG, no es texto visible
}

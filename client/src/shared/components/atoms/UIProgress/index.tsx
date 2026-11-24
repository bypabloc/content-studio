/**
 * Barra de progreso de un trabajo: un `progressbar` con su valor entre 0 y 1 (lo que hacía el `progress` nativo) y su
 * nombre por props. Es un átomo, así que puede usar `div` (spec 008, D-4).
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIProgress({ value, label }: { value: number; label: string }): React.JSX.Element {
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={1}
      aria-valuenow={value}
      className="h-2 w-full overflow-hidden rounded-full bg-muted"
    >
      <div className="h-full bg-primary transition-[width]" style={{ width: `${value * 100}%` }} />
    </div>
  )
}

import { useVirtualizer } from '@tanstack/react-virtual'
import { type ReactNode, useRef } from 'react'

import { UIBox } from '../../atoms/UIBox'

type Props = {
  /** Nombre accesible de la lista. */
  label: string
  count: number
  /** Alto fijo de cada fila, en píxeles. */
  rowHeight: number
  /** Alto visible de la lista, en píxeles. */
  height: number
  renderRow: (index: number) => ReactNode
}

/**
 * Lista de filas virtuales (spec 020, AC-9): con miles de filas, solo las visibles (y unas pocas de margen) están en el DOM.
 * Cada fila es un ítem de lista con su alto fijo; el desplazamiento lo maneja `@tanstack/react-virtual`.
 */
export function UIVirtualList({ label, count, rowHeight, height, renderRow }: Props): React.JSX.Element {
  const scroller = useRef<HTMLDivElement>(null)
  // El objeto de filas virtuales cambia en cada desplazamiento a propósito: el componente se vuelve a dibujar sin memorizar.
  // oxlint-disable-next-line react/incompatible-library
  const virtualizer = useVirtualizer({
    count,
    getScrollElement: () => scroller.current,
    estimateSize: () => rowHeight,
    overscan: 8,
    initialRect: { width: 0, height },
    // El alto es fijo (`height`): si el contenedor aún no tiene medidas (o el entorno no las da), vale ese alto.
    observeElementRect: (instance, notify) => {
      // La lista solo observa cuando ya tiene el contenedor: aquí nunca es null.
      const element = instance.scrollElement as HTMLDivElement
      const measure = () => {
        const rect = element.getBoundingClientRect()
        notify({ width: rect.width, height: rect.height || height })
      }
      measure()
      const observer = new ResizeObserver(measure)
      observer.observe(element)
      return () => observer.disconnect()
    },
  })
  return (
    <UIBox ref={scroller} className="overflow-auto" style={{ height }}>
      <UIBox role="list" aria-label={label} className="relative w-full" style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((row) => (
          <UIBox
            key={row.key}
            role="listitem"
            className="absolute inset-x-0"
            style={{ top: row.start, height: rowHeight }}
          >
            {renderRow(row.index)}
          </UIBox>
        ))}
      </UIBox>
    </UIBox>
  )
}

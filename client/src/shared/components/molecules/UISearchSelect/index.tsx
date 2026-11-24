import { lazy, Suspense, useEffect, useRef } from 'react'

import { UIFixedValue } from '../../atoms/UIFixedValue'
import { UISkeleton } from '../../atoms/UISkeleton'
import type { SearchSelectProps } from './Picker'

// Bajo demanda: el combobox (Base UI) solo se descarga con más de una opción; así
// ninguna pantalla que lo importe lo suma a su JS inicial (budget.json).
const Picker = lazy(async () => ({ default: (await import('./Picker')).SearchSelectPicker }))

/**
 * Selector de un valor con buscador (combobox): el campo muestra la opción
 * elegida; al escribir filtra las opciones por su texto, las flechas las
 * recorren, Enter o clic elige y Escape cierra. Cada opción puede llevar una
 * descripción. Opción única: con 1 opción muestra UIFixedValue y notifica
 * `onChange` una sola vez, sin descargar el combobox. Con más opciones lo
 * descarga bajo demanda y reserva su alto con un esqueleto. A diferencia de
 * `UICombobox` (agrega ítems y limpia el texto), conserva el valor elegido.
 *
 * @author Pablo Contreras
 * @since 2026/10/03
 * @since 2026/11/19
 */
export function UISearchSelect(props: SearchSelectProps): React.JSX.Element {
  const { label, options, onChange } = props
  const single = options.length === 1 ? options[0] : undefined
  const notified = useRef(false)

  useEffect(() => {
    if (single && !notified.current) {
      notified.current = true
      onChange(single.value)
    }
  }, [single, onChange])

  if (single) return <UIFixedValue label={label} value={single.label} />

  // Alto del esqueleto = etiqueta (caption 1,45) + separación (0,375 rem) + campo (min-h-12).
  return (
    <Suspense fallback={<UISkeleton className="h-[4.64rem] w-full rounded-xl" />}>
      <Picker {...props} />
    </Suspense>
  )
}

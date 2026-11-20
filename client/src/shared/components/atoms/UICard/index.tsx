import { cn } from 'cn'
import type { ComponentProps } from 'react'

import { Card } from '../../shadcn/card'

/**
 * Tarjeta de superficie con borde, radio amplio y elevación suave; se
 * expone como región (etiquetarla con `aria-label` o `aria-labelledby`).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UICard({ className, ...props }: ComponentProps<typeof Card>): React.JSX.Element {
  return <Card role="region" className={cn('@container w-full gap-0 p-6 sm:p-8', CARD_SURFACE, className)} {...props} />
}

/** Superficie de tarjeta (fondo, radio, elevación y borde): la comparten `UICard` y las piezas que no pueden ser un bloque, como la ficha de fila de `UIRowTable`. */
export const CARD_SURFACE = 'rounded-2xl bg-card shadow-ui ring-1 ring-border'

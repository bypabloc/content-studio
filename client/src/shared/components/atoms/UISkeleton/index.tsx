import { cn } from 'cn'

import { Skeleton } from '../../shadcn/skeleton'

/**
 * Bloque de carga que reserva el espacio del contenido final (evita CLS).
 * Oculto a lectores de pantalla: el anuncio lo hace `UIStatus`.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UISkeleton({ className }: { className?: string }): React.JSX.Element {
  return <Skeleton aria-hidden="true" className={cn('rounded-lg bg-border motion-reduce:animate-none', className)} />
}

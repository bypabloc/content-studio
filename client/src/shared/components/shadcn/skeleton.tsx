/**
 * Bloque de carga de shadcn. Lo envuelve `UISkeleton`.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */

import { cn } from "cn"

/** Bloque animado que reserva el espacio del contenido. */
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton }

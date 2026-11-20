/**
 * Indicador de carga de shadcn (ícono de lucide animado).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */

import { cn } from "cn"
import { Loader2Icon } from "lucide-react"

// shadcn-patch: el nombre accesible llega por `label` (i18n), sin "Loading" fijo.
/** Spinner con `role="status"` y nombre accesible por `label`. */
function Spinner({ className, label, ...props }: React.ComponentProps<"svg"> & { label: string }) {
  return (
    <Loader2Icon data-slot="spinner" role="status" aria-label={label} className={cn("size-4 animate-spin", className)} {...props} />
  )
}

export { Spinner }

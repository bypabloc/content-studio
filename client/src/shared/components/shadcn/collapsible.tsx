
/**
 * Collapsible de shadcn (Base UI Collapsible): raíz, disparador y panel. Lo envuelve `UICollapsible`.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 */
import { Collapsible as CollapsiblePrimitive } from "@base-ui/react/collapsible"

/** Raíz del plegable (abierto o cerrado). */
function Collapsible({ ...props }: CollapsiblePrimitive.Root.Props) {
  return <CollapsiblePrimitive.Root data-slot="collapsible" {...props} />
}

/** Botón que abre o cierra el panel (`aria-expanded`). */
function CollapsibleTrigger({ ...props }: CollapsiblePrimitive.Trigger.Props) {
  return (
    <CollapsiblePrimitive.Trigger data-slot="collapsible-trigger" {...props} />
  )
}

/** Panel plegable; se oculta al cerrar. */
function CollapsibleContent({ ...props }: CollapsiblePrimitive.Panel.Props) {
  return (
    <CollapsiblePrimitive.Panel data-slot="collapsible-content" {...props} />
  )
}

export { Collapsible, CollapsibleTrigger, CollapsibleContent }

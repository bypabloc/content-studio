
/**
 * Componentes shadcn para paneles flotantes accesibles basados en Base UI.
 *
 * @author Pablo Contreras
 * @since 2026/10/19
 */
import { Popover as PopoverPrimitive } from "@base-ui/react/popover"
import { cn } from "cn"

/** Raíz controlada o no controlada del popover. */
function Popover({ ...props }: PopoverPrimitive.Root.Props) {
  return <PopoverPrimitive.Root data-slot="popover" {...props} />
}

/** Disparador del popover. */
function PopoverTrigger({ ...props }: PopoverPrimitive.Trigger.Props) {
  return <PopoverPrimitive.Trigger data-slot="popover-trigger" {...props} />
}

/** Panel flotante del popover, ubicado respecto a su disparador o ancla. */
function PopoverContent({
  className,
  anchor,
  align,
  alignOffset,
  side,
  sideOffset,
  collisionPadding,
  collisionAvoidance,
  children,
  ...props
}: PopoverPrimitive.Popup.Props &
  // shadcn-patch: deja fijar collisionAvoidance para que un panel con lado fijo no salte al otro lado.
  Pick<PopoverPrimitive.Positioner.Props, "align" | "alignOffset" | "side" | "sideOffset" | "collisionPadding" | "collisionAvoidance"> & {
    anchor?: PopoverPrimitive.Positioner.Props["anchor"]
  }) {
  return (
    <PopoverPrimitive.Portal>
      <PopoverPrimitive.Positioner
        anchor={anchor}
        align={align}
        alignOffset={alignOffset}
        side={side}
        sideOffset={sideOffset}
        collisionPadding={collisionPadding}
        collisionAvoidance={collisionAvoidance}
        className="isolate z-50"
        data-slot="popover-positioner"
      >
        <PopoverPrimitive.Popup
          data-slot="popover-content"
          className={cn(
            // shadcn-patch: añade el anillo ui-focus, la animación estándar y el límite al espacio visible (con scroll propio).
            "z-50 max-h-(--available-height) max-w-(--available-width) min-w-48 overflow-y-auto overscroll-contain rounded-xl bg-popover p-4 text-popover-foreground shadow-ui-lg ring-1 ring-foreground/10 outline-none focus-visible:ui-focus motion-safe:animate-ui-pop",
            className,
          )}
          {...props}
        >
          {children}
        </PopoverPrimitive.Popup>
      </PopoverPrimitive.Positioner>
    </PopoverPrimitive.Portal>
  )
}

export { Popover, PopoverContent, PopoverTrigger }

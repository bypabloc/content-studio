/**
 * Combobox de shadcn (Base UI Combobox): campo de búsqueda con lista de
 * resultados navegable por teclado (flechas, Enter, Escape). Lo envuelve
 * `UICombobox`.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 */


import { Combobox as ComboboxPrimitive } from "@base-ui/react"
import { cn } from "cn"

import { Input } from "./input"

/** Raíz del combobox (estado, valor y texto buscado). */
const Combobox = ComboboxPrimitive.Root

// shadcn-patch: sin InputGroup, disparador ni botón de limpiar (el buscador
// solo agrega ítems); el input es el `Input` del proyecto.
/** Campo de búsqueda del combobox con `data-slot="combobox-input"`. */
function ComboboxInput({ className, ...props }: ComboboxPrimitive.Input.Props) {
  return (
    <ComboboxPrimitive.Input
      data-slot="combobox-input"
      render={<Input />}
      className={cn(className)}
      {...props}
    />
  )
}

// shadcn-patch: animación de entrada y salida del popup (D4): fade y zoom 95 como dropdown-menu, con motion-safe: y duration-150.
/** Panel flotante anclado al input (portal + posicionador). */
function ComboboxContent({
  className,
  side = "bottom",
  sideOffset = 6,
  align = "start",
  ...props
}: ComboboxPrimitive.Popup.Props &
  Pick<ComboboxPrimitive.Positioner.Props, "side" | "align" | "sideOffset">) {
  return (
    <ComboboxPrimitive.Portal>
      <ComboboxPrimitive.Positioner
        side={side}
        sideOffset={sideOffset}
        align={align}
        className="isolate z-50"
      >
        <ComboboxPrimitive.Popup
          data-slot="combobox-content"
          className={cn(
            "group/combobox-content relative max-h-(--available-height) w-(--anchor-width) max-w-(--available-width) origin-(--transform-origin) overflow-hidden rounded-lg bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10 duration-150 ease-ui-out motion-safe:data-[side=bottom]:slide-in-from-top-2 motion-safe:data-[side=left]:slide-in-from-right-2 motion-safe:data-[side=right]:slide-in-from-left-2 motion-safe:data-[side=top]:slide-in-from-bottom-2 motion-safe:data-open:animate-in motion-safe:data-open:fade-in-0 motion-safe:data-open:zoom-in-95 motion-safe:data-closed:animate-out motion-safe:data-closed:fade-out-0 motion-safe:data-closed:zoom-out-95",
            className
          )}
          {...props}
        />
      </ComboboxPrimitive.Positioner>
    </ComboboxPrimitive.Portal>
  )
}

/** Lista de resultados con scroll propio. */
function ComboboxList({ className, ...props }: ComboboxPrimitive.List.Props) {
  return (
    <ComboboxPrimitive.List
      data-slot="combobox-list"
      className={cn(
        "max-h-72 scroll-py-1 overflow-y-auto overscroll-contain p-1 data-empty:p-0",
        className
      )}
      {...props}
    />
  )
}

// shadcn-patch: sin indicador de elegido (el buscador no conserva valor).
/** Opción resaltable de la lista. */
function ComboboxItem({ className, ...props }: ComboboxPrimitive.Item.Props) {
  return (
    <ComboboxPrimitive.Item
      data-slot="combobox-item"
      className={cn(
        "relative flex w-full cursor-default items-center gap-2 rounded-md px-2 py-1.5 text-sm outline-hidden select-none data-highlighted:bg-accent data-highlighted:text-accent-foreground data-disabled:pointer-events-none data-disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
}

/** Mensaje cuando no hay resultados. */
function ComboboxEmpty({ className, ...props }: ComboboxPrimitive.Empty.Props) {
  return (
    <ComboboxPrimitive.Empty
      data-slot="combobox-empty"
      className={cn(
        "hidden w-full justify-center py-2 text-center text-sm text-muted-foreground group-data-empty/combobox-content:flex",
        className
      )}
      {...props}
    />
  )
}

// shadcn-patch: grupos de resultados (Base UI `Combobox.Group`) para agrupar por capítulo; sin estilo propio.
/** Grupo de opciones que comparte un encabezado (`ComboboxLabel`). */
function ComboboxGroup({ className, ...props }: ComboboxPrimitive.Group.Props) {
  return (
    <ComboboxPrimitive.Group
      data-slot="combobox-group"
      className={cn(className)}
      {...props}
    />
  )
}

// shadcn-patch: encabezado del grupo con la tipografía de caption del proyecto.
/** Encabezado de un `ComboboxGroup`; el grupo toma su nombre accesible de este texto. */
function ComboboxLabel({ className, ...props }: ComboboxPrimitive.GroupLabel.Props) {
  return (
    <ComboboxPrimitive.GroupLabel
      data-slot="combobox-label"
      className={cn(
        "ui-typography-caption px-3 pt-2 pb-1 font-bold text-muted-foreground",
        className
      )}
      {...props}
    />
  )
}

// shadcn-patch: colección de ítems dentro de un grupo (Base UI `Combobox.Collection`), que usa los `items` del grupo.
/** Renderiza un ítem por cada elemento del grupo que la contiene. */
function ComboboxCollection(props: ComboboxPrimitive.Collection.Props) {
  return <ComboboxPrimitive.Collection {...props} />
}

export {
  Combobox,
  ComboboxCollection,
  ComboboxInput,
  ComboboxContent,
  ComboboxGroup,
  ComboboxLabel,
  ComboboxList,
  ComboboxItem,
  ComboboxEmpty,
}

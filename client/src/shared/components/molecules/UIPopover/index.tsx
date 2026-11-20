/**
 * Panel flotante controlado y anclado a un elemento de la interfaz.
 *
 * @author Pablo Contreras
 * @since 2026/10/19
 * @since 2026/11/19
 */
import type { ReactNode, RefObject } from 'react'

import { Popover, PopoverContent } from '../../shadcn/popover'

export type UIPopoverProps = {
  anchor: RefObject<HTMLElement | null>
  open: boolean
  onOpenChange: (open: boolean) => void
  label: string
  side?: 'top' | 'bottom'
  align?: 'start' | 'center' | 'end'
  children: ReactNode
}

/**
 * Muestra contenido flotante con nombre accesible y foco devuelto al ancla, sin pasar del espacio visible.
 * Con `side` fijo el panel no cambia de lado: si no cabe, lo limita la altura disponible y hace scroll.
 */
export function UIPopover({ anchor, open, onOpenChange, label, side, align, children }: UIPopoverProps): React.JSX.Element {
  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverContent
        anchor={anchor}
        aria-label={label}
        finalFocus={anchor}
        side={side}
        align={align}
        sideOffset={8}
        collisionPadding={8}
        collisionAvoidance={side ? { side: 'none' } : undefined}
      >
        {children}
      </PopoverContent>
    </Popover>
  )
}

import type { ReactNode, RefObject } from 'react'

import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../../shadcn/dialog'

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  closeLabel: string
  children: ReactNode
  footer?: ReactNode
  finalFocus?: RefObject<HTMLElement | null>
  modal?: boolean
}

/**
 * Diálogo controlado con Escape y botón de cierre
 * nombrado, título como nombre accesible y descripción opcional; el pie
 * recibe las acciones. `modal` controla si bloquea el fondo y `finalFocus`
 * indica a qué elemento vuelve el foco al cerrar (por defecto, al que tenía
 * el foco al abrir).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UIDialog({
  open,
  onOpenChange,
  title,
  description,
  closeLabel,
  children,
  footer,
  finalFocus,
  modal = true,
}: Props): React.JSX.Element {
  return (
    <Dialog open={open} onOpenChange={onOpenChange} modal={modal}>
      <DialogContent
        closeLabel={closeLabel}
        finalFocus={finalFocus}
        showOverlay={modal}
        className="max-h-[calc(100dvh-2rem)] gap-6 overflow-y-auto rounded-2xl bg-card p-6 text-foreground shadow-ui-lg sm:max-w-lg [&>[data-slot=dialog-close]]:size-11"
      >
        <DialogHeader className="pr-10">
          <DialogTitle className="ui-typography-subtitle-2 text-foreground">{title}</DialogTitle>
          {description ? <DialogDescription className="ui-typography-body text-foreground-secondary">{description}</DialogDescription> : null}
        </DialogHeader>
        {children}
        {footer ? <DialogFooter className="-mx-6 -mb-6 rounded-b-2xl bg-muted px-6 py-4">{footer}</DialogFooter> : null}
      </DialogContent>
    </Dialog>
  )
}

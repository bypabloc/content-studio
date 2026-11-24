import { cn } from 'cn'
import { useState } from 'react'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../../shadcn/alert-dialog'

import { type IconName } from '../../atoms/UIIcon'
import { UIButton } from '../../atoms/UIButton'

type Props = {
  triggerLabel?: string
  triggerIcon?: IconName
  title: string
  description: string
  confirmLabel: string
  cancelLabel: string
  destructive?: boolean
  pending?: boolean
  onConfirm: () => void
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

/**
 * Acción que pide confirmación en un diálogo (`alertdialog`): el disparador
 * queda ocupado mientras `pending`, Confirmar y Cancelar cierran (el foco
 * vuelve al disparador) y
 * `destructive` marca la acción como peligrosa. Con `open`/`onOpenChange`
 * queda controlado y sin disparador (p. ej. abierto desde un menú de fila).
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */
export function UIConfirmDialog({ triggerLabel, triggerIcon, title, description, confirmLabel, cancelLabel, destructive = false, pending = false, onConfirm, open: controlled, onOpenChange }: Props): React.JSX.Element {
  const [local, setLocal] = useState(false)
  const open = controlled ?? local
  const setOpen = (next: boolean): void => {
    setLocal(next)
    onOpenChange?.(next)
  }
  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      {triggerLabel ? <AlertDialogTrigger render={<UIButton variant="secondary" icon={triggerIcon} loading={pending} />}>{triggerLabel}</AlertDialogTrigger> : null}
      <AlertDialogContent className="max-w-md gap-6 rounded-2xl p-6 sm:max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="ui-typography-subtitle-2 text-foreground">{title}</AlertDialogTitle>
          <AlertDialogDescription className="ui-typography-body text-foreground-secondary">{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel className="ui-typography-body min-h-11 rounded-xl px-4 font-bold">{cancelLabel}</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              setOpen(false)
              onConfirm()
            }}
            variant={destructive ? 'destructive' : 'default'}
            className={cn('ui-typography-body min-h-11 rounded-xl px-4 font-bold', destructive && 'bg-destructive text-card hover:bg-destructive/90 dark:bg-destructive dark:hover:bg-destructive/90')}
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

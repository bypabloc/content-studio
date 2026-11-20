import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../../shadcn/alert-dialog'

import { UIButton } from '../../atoms/UIButton'
import { UIForm } from '../../atoms/UIForm'

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  cancelLabel: string
  destructive?: boolean
  pending?: boolean
  confirmDisabled?: boolean
  onSubmit: () => void
  children: React.ReactNode
}

/**
 * Diálogo modal con campos: envía un formulario al confirmar y deshabilita la acción mientras `pending`.
 * Confirmar no cierra el diálogo; lo cierra quien lo abre cuando tiene el resultado. Cancelar y Escape
 * llaman a `onOpenChange(false)` sin enviar. Usa el diálogo de alerta de shadcn porque ops no tiene `dialog`.
 *
 * @author Pablo Contreras
 * @since 2026/10/31
 */
export function UIFormDialog({ open, onOpenChange, title, description, confirmLabel, cancelLabel, destructive = false, pending = false, confirmDisabled = false, onSubmit, children }: Props): React.JSX.Element {
  return (
    <AlertDialog open={open} onOpenChange={(next) => onOpenChange(next)}>
      <AlertDialogContent className="max-w-md gap-6 rounded-2xl p-6 sm:max-w-md">
        <UIForm
          onSubmit={(event) => {
            event.preventDefault()
            onSubmit()
          }}
        >
          <AlertDialogHeader>
            <AlertDialogTitle className="ui-typography-subtitle-2 text-foreground">{title}</AlertDialogTitle>
            <AlertDialogDescription className="ui-typography-body text-foreground-secondary">{description}</AlertDialogDescription>
          </AlertDialogHeader>
          {children}
          <AlertDialogFooter>
            <AlertDialogCancel type="button" className="ui-typography-body min-h-11 rounded-xl px-4 font-bold">
              {cancelLabel}
            </AlertDialogCancel>
            <UIButton type="submit" variant={destructive ? 'danger' : 'primary'} loading={pending} disabled={confirmDisabled}>
              {confirmLabel}
            </UIButton>
          </AlertDialogFooter>
        </UIForm>
      </AlertDialogContent>
    </AlertDialog>
  )
}

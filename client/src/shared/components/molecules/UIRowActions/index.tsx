import { cn } from 'cn'

import { Button } from '../../shadcn/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../shadcn/dropdown-menu'

import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { UIBox } from '../../atoms/UIBox'

/** Acción de una fila; deshabilitada muestra `disabledReason` bajo el nombre. */
export type UIRowAction = {
  key: string
  label: string
  icon: IconName
  onSelect: () => void
  analyticsId?: 'document.download' | 'users.deactivate'
  destructive?: boolean
  disabled?: boolean
  disabledReason?: string
}

type Props = { label: string; items: UIRowAction[] }

/**
 * Menú de acciones por fila: disparador de solo ícono con nombre accesible
 * propio de la fila (p. ej. "Acciones de Ana Ruiz"), ítems de 44px y el
 * motivo visible cuando una acción no está disponible.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIRowActions({ label, items }: Props): React.JSX.Element {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={<Button variant="ghost" aria-label={label} className="size-11 cursor-pointer rounded-xl text-foreground-secondary hover:text-foreground focus-visible:ui-focus" />}
      >
        <UIIcon name="ellipsis" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-56">
        {items.map((item) => (
          <DropdownMenuItem
            key={item.key}
            disabled={item.disabled}
            variant={item.destructive ? 'destructive' : 'default'}
            onClick={item.onSelect}
            data-analytics={item.analyticsId}
            className={cn('ui-typography-body min-h-11 cursor-pointer gap-2 px-2', item.disabled && 'items-start py-2')}
          >
            <UIIcon name={item.icon} className="mt-0.5" />
            <UIBox as="span" className="flex flex-col">
              {item.label}
              {item.disabled && item.disabledReason ? <UIBox as="span" className="ui-typography-caption text-muted-foreground">{item.disabledReason}</UIBox> : null}
            </UIBox>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

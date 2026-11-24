import type { ReactNode } from 'react'

import { cn } from 'cn'

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../../shadcn/collapsible'

import { UIIcon } from '../../atoms/UIIcon'

type Props = {
  trigger: string
  children: ReactNode
  defaultOpen?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
  /** Deja el contenido montado al plegar (sus campos siguen en el formulario); por defecto se desmonta. */
  keepMounted?: boolean
}

/**
 * Plegable: botón con chevron (`aria-expanded`, área táctil de 44px) que
 * muestra u oculta su contenido. Cerrado por defecto.
 *
 * @author Pablo Contreras
 * @since 2026/09/28
 * @since 2026/11/19
 */
export function UICollapsible({ trigger, children, defaultOpen = false, open, onOpenChange, keepMounted = false }: Props): React.JSX.Element {
  return (
    <Collapsible defaultOpen={defaultOpen} open={open} onOpenChange={onOpenChange} className="flex w-full flex-col gap-2">
      <CollapsibleTrigger
        className={cn(
          'group ui-typography-body inline-flex min-h-11 w-fit cursor-pointer items-center gap-2 whitespace-nowrap rounded-xl px-2',
          'font-bold text-accent-foreground transition-colors duration-200 hover:bg-accent focus-visible:ui-focus active:bg-accent motion-reduce:transition-none',
        )}
      >
        <UIIcon name="chevron-down" className="size-5 transition-transform duration-200 group-data-[panel-open]:rotate-180 motion-reduce:transition-none" />
        {trigger}
      </CollapsibleTrigger>
      <CollapsibleContent
        keepMounted={keepMounted}
        className={cn(
          'ui-typography-body h-(--collapsible-panel-height) overflow-hidden px-2 text-foreground-secondary transition-[height] duration-150',
          'ease-ui-out motion-reduce:transition-none motion-safe:animate-ui-fade data-starting-style:h-0 data-ending-style:h-0',
        )}
      >
        {children}
      </CollapsibleContent>
    </Collapsible>
  )
}

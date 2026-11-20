import type { ReactNode } from 'react'

import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '../../shadcn/sheet'

import { UIBox } from '../../atoms/UIBox'
import { UIButton } from '../../atoms/UIButton'

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onOpenChangeComplete?: (open: boolean) => void
  title: string
  description?: string
  closeLabel: string
  sections: ReactNode[]
}

/**
 * Hoja modal inferior con título, cierre accesible y bloques separados.
 * Base UI controla el foco, Escape, el retorno del foco y el fin de la animación.
 *
 * @author Pablo Contreras
 * @since 2026/10/25
 */
export function UIBottomSheet({ open, onOpenChange, onOpenChangeComplete, title, description, closeLabel, sections }: Props): React.JSX.Element {
  return (
    <Sheet open={open} onOpenChange={onOpenChange} onOpenChangeComplete={onOpenChangeComplete}>
      <SheetContent
        side="bottom"
        closeLabel={closeLabel}
        showCloseButton={false}
        className="max-h-[85dvh] gap-0 overflow-y-auto rounded-t-2xl border-0 bg-popover p-0 pb-[max(1rem,env(safe-area-inset-bottom))] motion-safe:animate-ui-pop motion-reduce:transition-none"
      >
        <UIBox as="span" aria-hidden="true" className="mx-auto mt-3 h-1.5 w-10 rounded-full bg-border" />
        <SheetHeader className="relative gap-1 px-4 pt-3 pb-4 text-left">
          <SheetTitle className="ui-typography-subtitle-2 text-foreground">{title}</SheetTitle>
          {description ? <SheetDescription className="ui-typography-body text-foreground-secondary">{description}</SheetDescription> : null}
          <SheetClose
            render={
              <UIButton variant="ghost" icon="x" aria-label={closeLabel} className="absolute top-2 right-2 size-11 rounded-xl px-0 text-foreground focus-visible:ui-focus hover:bg-muted" />
            }
          />
        </SheetHeader>
        {sections.map((section, index) => (
          <UIBox key={index} data-slot="bottom-sheet-section" className={`px-4 py-4 ${index > 0 ? 'border-t border-border' : ''}`}>
            {section}
          </UIBox>
        ))}
      </SheetContent>
    </Sheet>
  )
}

import type { ReactNode } from 'react'

import { useSectionId } from '@/shared/hooks/useSectionId'

import { UIBox } from '../../atoms/UIBox'
import { type IconName, UIIcon } from '../../atoms/UIIcon'
import { UILink } from '../../atoms/UILink'
import { UITooltip } from '../../atoms/UITooltip'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from '../../shadcn/sidebar'
import { TooltipProvider } from '../../shadcn/tooltip'

const MAIN_ID = 'content'
/** Oculta un bloque cuando la barra está en íconos: la raíz de la barra lleva `data-collapsible="icon"`. */
const HIDDEN_WHEN_COLLAPSED = 'group-data-[collapsible=icon]:hidden'

/** Una sección del menú: `group` la agrupa y `id` va en el hash (`#/<id>`). */
export type NavEntry = { id: string; group: string; label: string; icon: IconName }

/** Textos que llegan por props, como en el resto de los organismos (spec 008, D-3). */
type Labels = { skip: string; toggle: string; title: string }

type Props = {
  /** El nombre de la app: se oculta cuando la barra está en íconos. */
  brand: ReactNode
  nav: readonly NavEntry[]
  /** El panel de la cola: va bajo las secciones y se oculta al colapsar (spec 008, D-7). */
  aside?: ReactNode
  /** El pie de la barra: el tema y la versión. */
  footer?: ReactNode
  /** Estado guardado de la barra (`ui.sidebar.collapsed`). Sin él, la barra decide sola y empieza abierta. */
  collapsed?: boolean
  onCollapsedChange?: (collapsed: boolean) => void
  labels: Labels
  children: ReactNode
}

/**
 * Estructura de la ventana: enlace para saltar al contenido, y una barra lateral con su botón (y Ctrl+B) para
 * colapsarla, las secciones agrupadas (la activa según el hash), el panel de la cola y el pie. Colapsada, queda en
 * íconos y cada sección muestra su nombre en un texto de ayuda. No tiene modo móvil: la ventana de Tauri tiene un
 * ancho mínimo de escritorio (spec 008, D-7).
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIAppShell({ brand, nav, aside, footer, collapsed, onCollapsedChange, labels, children }: Props): React.JSX.Element {
  const active = useSectionId()
  const groups = [...new Set(nav.map((entry) => entry.group))]

  return (
    <TooltipProvider>
      <SidebarProvider
        className="select-none"
        open={collapsed === undefined ? undefined : !collapsed}
        onOpenChange={(open) => onCollapsedChange?.(!open)}
      >
        <UILink
          href={`#${MAIN_ID}`}
          className="sr-only rounded-lg bg-card font-bold text-foreground shadow-ui-lg focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2.5 focus-visible:ui-focus"
        >
          {labels.skip}
        </UILink>
        <UIBox as="aside" className="contents">
          {/* La hoja móvil de la barra no se usa (spec 008, D-7): sus textos salen de las etiquetas de la barra. */}
          <Sidebar collapsible="icon" labels={{ title: labels.title, description: labels.title, close: labels.toggle }}>
            <SidebarHeader>
              <UIBox className="flex items-center justify-between gap-2">
                <UIBox className={HIDDEN_WHEN_COLLAPSED}>{brand}</UIBox>
                {/* Solo ícono con su texto de ayuda (spec 009, D-4): el trigger de shadcn no lo trae, y no se edita shadcn/. */}
                <UITooltip content={labels.toggle}>
                  <SidebarTrigger label={labels.toggle} className="size-11 rounded-xl focus-visible:ui-focus" />
                </UITooltip>
              </UIBox>
            </SidebarHeader>
            <SidebarContent>
              <UIBox as="nav" aria-label={labels.title} className="flex flex-col gap-4">
                {groups.map((group) => (
                  <SidebarGroup key={group}>
                    <SidebarGroupLabel>{group}</SidebarGroupLabel>
                    <SidebarMenu>
                      {nav
                        .filter((entry) => entry.group === group)
                        .map((entry) => (
                          <SidebarMenuItem key={entry.id}>
                            <SidebarMenuButton
                              isActive={entry.id === active}
                              tooltip={{ children: entry.label, role: 'tooltip' }}
                              render={<UILink href={`#/${entry.id}`} aria-current={entry.id === active ? 'page' : undefined} />}
                            >
                              <UIIcon name={entry.icon} />
                              <UIBox as="span">{entry.label}</UIBox>
                            </SidebarMenuButton>
                          </SidebarMenuItem>
                        ))}
                    </SidebarMenu>
                  </SidebarGroup>
                ))}
              </UIBox>
              {/* Mismo margen que las secciones (SidebarGroup p-2 + SidebarMenuButton px-2): la cola se alinea con su texto. */}
              {aside ? <UIBox className={`${HIDDEN_WHEN_COLLAPSED} px-4 py-2`}>{aside}</UIBox> : null}
            </SidebarContent>
            {footer ? <SidebarFooter>{footer}</SidebarFooter> : null}
          </Sidebar>
        </UIBox>
        <UIBox as="main" id={MAIN_ID} tabIndex={-1} className="flex min-w-0 flex-1 flex-col gap-2 p-6 focus:outline-none">
          {children}
        </UIBox>
      </SidebarProvider>
    </TooltipProvider>
  )
}

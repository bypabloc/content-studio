import type { ReactNode } from 'react'
import type { IconName } from '../../atoms/UIIcon'

/** Ubicaciones admitidas para la barra flotante. */
export const FLOATING_TOOLBAR_PLACEMENTS = [
  'top-left',
  'top',
  'top-right',
  'left',
  'right',
  'bottom-left',
  'bottom',
  'bottom-right',
] as const

/** Posición de la barra respecto al viewport. */
export type FloatingToolbarPlacement = (typeof FLOATING_TOOLBAR_PLACEMENTS)[number]

/** Acción genérica de la barra. */
export type FloatingToolbarItem = {
  id: string
  label: string
  icon: IconName
  notice?: string
  separatorBefore?: boolean
}

/** Propiedades de la barra flotante genérica. */
export type UIFloatingToolbarProps = {
  label: string
  showLabel: string
  closeLabel: (item: string) => string
  items: FloatingToolbarItem[]
  placement: FloatingToolbarPlacement
  bottomNavOffset?: boolean
  autoHide: boolean
  activeId: string | null
  onActiveChange: (id: string | null) => void
  children: ReactNode
}

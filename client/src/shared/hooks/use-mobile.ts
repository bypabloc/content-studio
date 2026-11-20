/**
 * Hook de shadcn para detectar el viewport mobile (< 768 px) y seguir sus
 * cambios. Lo usa el Sidebar.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 */

import * as React from "react"

const MOBILE_BREAKPOINT = 768
const QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`

const subscribe = (onChange: () => void): (() => void) => {
  const mql = window.matchMedia(QUERY)
  mql.addEventListener("change", onChange)
  return () => mql.removeEventListener("change", onChange)
}

// shadcn-patch: useSyncExternalStore en vez de setState dentro de un efecto.
/** True si el viewport es menor a 768 px (el sidebar pasa a panel lateral). */
export function useIsMobile(): boolean {
  return React.useSyncExternalStore(
    subscribe,
    () => window.innerWidth < MOBILE_BREAKPOINT,
    () => false
  )
}

/**
 * Preferencia de movimiento reducido del sistema (`prefers-reduced-motion`).
 * El hook devuelve `true` cuando el usuario pide menos animación y sigue sus
 * cambios sin recargar. Está pensado para las animaciones que dirige
 * JavaScript, como las gráficas de `UIChart`; las clases CSS ya respetan la
 * preferencia con `motion-safe:` y con la regla global de `globals.css`.
 *
 * @author Pablo Contreras
 * @since 2026/10/13
 */

import { useSyncExternalStore } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

/** Media query de la preferencia, o `null` si no hay `window` ni `matchMedia`. */
function media(): MediaQueryList | null {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return null
  return window.matchMedia(QUERY)
}

/** Avisa cuando cambia la preferencia; sin `matchMedia` no hay nada que escuchar. */
function subscribe(onChange: () => void): () => void {
  const mql = media()
  if (!mql) return () => {}
  mql.addEventListener('change', onChange)
  return () => mql.removeEventListener('change', onChange)
}

const getSnapshot = (): boolean => media()?.matches ?? false
const getServerSnapshot = (): boolean => false

/**
 * Dice si el usuario pide reducir el movimiento. Devuelve `false` en el
 * servidor y cuando el navegador no tiene `matchMedia`.
 *
 * @author Pablo Contreras
 * @since 2026/10/13
 */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}

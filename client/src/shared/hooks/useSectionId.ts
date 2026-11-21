import { useEffect, useState } from 'react'

/**
 * La sección del hash (`#/settings` → `settings`). Sigue los cambios del hash sin recargar. Vive en `shared/hooks`
 * porque lo usa `UIAppShell` (un organismo no puede importar de `app/`).
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function useSectionId(): string {
  const [hash, setHash] = useState(() => window.location.hash)

  useEffect(() => {
    const update = () => setHash(window.location.hash)
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])

  return hash.replace(/^#\//, '').split('?')[0]
}

import { useEffect, useState } from 'react';

/** La sección del hash (`#/settings` → `settings`). Sigue los cambios del hash sin recargar. */
export function useSectionId(): string {
  const [hash, setHash] = useState(() => window.location.hash);

  useEffect(() => {
    const update = () => setHash(window.location.hash);
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);

  return hash.replace(/^#\//, '');
}

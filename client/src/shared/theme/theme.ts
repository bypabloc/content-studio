export type ThemeMode = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

// La misma clave que `ui.theme` en la tabla settings: la caché solo adelanta el valor del server.
const CACHE_KEY = 'ui.theme';
const MODES: readonly ThemeMode[] = ['light', 'dark', 'system'];

/** La elección guardada en caché para pintar antes de que llegue la del server (D-4). Sin caché, `system`. */
export function readCachedTheme(): ThemeMode {
  try {
    const value = localStorage.getItem(CACHE_KEY);
    return MODES.find((mode) => mode === value) ?? 'system';
  } catch {
    return 'system';
  }
}

function cacheTheme(mode: ThemeMode): void {
  try {
    localStorage.setItem(CACHE_KEY, mode);
  } catch {
    // Sin almacenamiento la app pinta igual; solo se pierde el adelanto del siguiente arranque.
  }
}

export function resolveTheme(mode: ThemeMode, systemPrefersDark: boolean): ResolvedTheme {
  if (mode === 'system') return systemPrefersDark ? 'dark' : 'light';
  return mode;
}

/**
 * Pone o quita la clase `dark` en <html> y guarda la elección. Con `system` sigue al sistema; la función
 * que devuelve deja de seguirlo (al cambiar de modo o al desmontar).
 */
export function applyTheme(mode: ThemeMode, media: MediaQueryList, root: HTMLElement): () => void {
  cacheTheme(mode);
  const paint = () => root.classList.toggle('dark', resolveTheme(mode, media.matches) === 'dark');
  paint();
  if (mode !== 'system') return () => {};
  media.addEventListener('change', paint);
  return () => media.removeEventListener('change', paint);
}

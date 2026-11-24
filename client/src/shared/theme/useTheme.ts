import { getCurrentWindow } from '@tauri-apps/api/window';
import { useEffect } from 'react';
import { useSetting } from '@/shared/hooks/useSetting';
import { applyTheme, readCachedTheme, type ThemeMode } from './theme';

/** El tema de la app: lo guarda el server en `ui.theme`, lo pinta en <html> y avisa a la barra de la ventana. */
export function useTheme(): [ThemeMode, (mode: ThemeMode) => void] {
  const [mode, setMode] = useSetting<ThemeMode>('ui.theme', readCachedTheme());

  useEffect(
    () => applyTheme(mode, window.matchMedia('(prefers-color-scheme: dark)'), document.documentElement),
    [mode],
  );

  useEffect(() => {
    // Fuera de Tauri (vitest, el navegador) no hay ventana que avisar.
    if ('__TAURI_INTERNALS__' in window) void getCurrentWindow().setTheme(mode === 'system' ? null : mode);
  }, [mode]);

  return [mode, setMode];
}

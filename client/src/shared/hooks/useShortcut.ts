import { useEffect } from 'react';

/**
 * Un atajo como `mod+k`: `mod` es Ctrl (o Cmd), `shift` y `alt` son modificadores exactos, y lo último es la tecla.
 * Escucha en la ventana entera mientras el componente esté montado.
 */
export function useShortcut(combo: string, handler: (event: KeyboardEvent) => void): void {
  useEffect(() => {
    const parts = combo.toLowerCase().split('+');
    const key = parts[parts.length - 1];
    const wanted = { mod: parts.includes('mod'), shift: parts.includes('shift'), alt: parts.includes('alt') };
    const listener = (event: KeyboardEvent) => {
      const matches =
        event.key.toLowerCase() === key &&
        (event.ctrlKey || event.metaKey) === wanted.mod &&
        event.shiftKey === wanted.shift &&
        event.altKey === wanted.alt;
      if (matches) handler(event);
    };
    window.addEventListener('keydown', listener);
    return () => window.removeEventListener('keydown', listener);
  }, [combo, handler]);
}

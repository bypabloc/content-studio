import { getCurrentWebview } from '@tauri-apps/api/webview';
import { open } from '@tauri-apps/plugin-dialog';
import { useCallback, useEffect, useRef, useState } from 'react';

import { t } from '@/shared/i18n/t';

// Las APIs de Tauri existen solo dentro de la ventana: en el navegador de las pruebas, el hook no hace nada.
const inTauri = () => '__TAURI_INTERNALS__' in window;

export interface FilePathsOptions {
  /** Extensiones aceptadas, sin punto y sin distinguir mayúsculas (`mp4`, `wav`). */
  extensions: readonly string[];
  /** Recibe las rutas aceptadas, con el diálogo del sistema o soltadas sobre la ventana. */
  onPaths: (paths: string[]) => void;
  /** Recibe las rutas que no tienen una extensión aceptada, para avisar de ellas. */
  onRejected?: (paths: string[]) => void;
}

function extensionOf(path: string): string | undefined {
  return /\.([^./\\]+)$/.exec(path)?.[1]?.toLowerCase();
}

/**
 * Elegir o soltar archivos por ruta: el server necesita la ruta del disco (los trabajos leen el archivo), y el arrastre
 * HTML5 no la da. Devuelve `dragging` mientras hay algo sobre la ventana, para resaltar la zona.
 */
export function useFilePaths({ extensions, onPaths, onRejected }: FilePathsOptions) {
  const [dragging, setDragging] = useState(false);
  const latest = useRef({ extensions, onPaths, onRejected });
  useEffect(() => {
    latest.current = { extensions, onPaths, onRejected };
  });

  // Estable: lee lo último de `latest`, así que la suscripción de la ventana no se repite en cada render.
  const accept = useCallback((paths: string[]) => {
    const { extensions: allowed, onPaths: deliver, onRejected: reject } = latest.current;
    const accepted = paths.filter((path) => allowed.includes(extensionOf(path) ?? ''));
    const rejected = paths.filter((path) => !accepted.includes(path));
    if (accepted.length > 0) deliver(accepted);
    if (rejected.length > 0) reject?.(rejected);
  }, []);

  useEffect(() => {
    if (!inTauri()) return;
    let stop: (() => void) | undefined;
    void getCurrentWebview()
      .onDragDropEvent((event) => {
        const { type } = event.payload;
        if (type === 'enter' || type === 'over') setDragging(true);
        else setDragging(false);
        if (type === 'drop') accept(event.payload.paths);
      })
      .then((off) => {
        stop = off;
      });
    return () => stop?.();
  }, [accept]);

  return {
    dragging,
    pick: async () => {
      if (!inTauri()) return;
      const picked = await open({
        multiple: true,
        filters: [{ name: t('media.files.filter'), extensions: [...extensions] }],
      });
      if (picked) accept(Array.isArray(picked) ? picked : [picked]);
    },
  };
}

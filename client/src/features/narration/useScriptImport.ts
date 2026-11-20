import { getCurrentWebview } from '@tauri-apps/api/webview';
import { open } from '@tauri-apps/plugin-dialog';
import { useEffect } from 'react';
import { toast } from 'sonner';
import { t } from '@/shared/i18n/t';

/** Las extensiones que el server sabe leer como guion. */
const SCRIPT_EXTENSIONS = ['txt', 'json'];

// Las APIs de Tauri existen solo dentro de la ventana: en el navegador de las pruebas, este hook no hace nada.
const inTauri = () => '__TAURI_INTERNALS__' in window;

/** Separa las rutas en guiones (.txt y .json, sin distinguir mayúsculas) y en las que no lo son. */
export function splitScriptPaths(paths: string[]): { accepted: string[]; rejected: string[] } {
  const accepted: string[] = [];
  const rejected: string[] = [];
  for (const path of paths) {
    const extension = /\.([^./\\]+)$/.exec(path)?.[1]?.toLowerCase();
    (extension !== undefined && SCRIPT_EXTENSIONS.includes(extension) ? accepted : rejected).push(path);
  }
  return { accepted, rejected };
}

/** Pasa los guiones válidos a `onImport` y avisa de los demás: el error del catálogo, y no se importa ninguno. */
function acceptPaths(paths: string[], onImport: (paths: string[]) => void): void {
  const { accepted, rejected } = splitScriptPaths(paths);
  if (accepted.length > 0) onImport(accepted);
  if (rejected.length > 0) {
    const names = rejected.map((path) => path.split(/[\\/]/).pop() ?? path).join(', ');
    toast.error(t('narration.import.rejected', { names }));
  }
}

/**
 * Importa guiones por ruta: con «Importar» (el diálogo del sistema) o soltándolos sobre la ventana. Las rutas van
 * al server tal cual, porque los trabajos leen el archivo desde disco.
 */
export function useScriptImport(onImport: (paths: string[]) => void) {
  useEffect(() => {
    if (!inTauri()) return;
    let stop: (() => void) | undefined;
    void getCurrentWebview()
      .onDragDropEvent((event) => {
        if (event.payload.type === 'drop') acceptPaths(event.payload.paths, onImport);
      })
      .then((off) => {
        stop = off;
      });
    return () => stop?.();
  }, [onImport]);

  return {
    pick: async () => {
      if (!inTauri()) return;
      const picked = await open({
        multiple: true,
        filters: [{ name: t('narration.import.filter'), extensions: SCRIPT_EXTENSIONS }],
      });
      if (picked) acceptPaths(Array.isArray(picked) ? picked : [picked], onImport);
    },
  };
}

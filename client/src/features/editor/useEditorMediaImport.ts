import { useCallback, useEffect, useRef, useState } from 'react';

import { useApi } from '@/shared/api/context';

import { buildImportOperations } from './importMedia';
import type { Doc, Op } from './model/types';

interface Params {
  tracks: Doc['tracks'];
  trackCount: number;
  applyOp: (op: Op) => void;
  pendingAdd: string[];
  position: number;
  onAddHandled?: () => void;
}

/** Importa los medios solicitados en el cabezal y confirma cuando termina la lectura. */
export function useEditorMediaImport({
  tracks,
  trackCount,
  applyOp,
  pendingAdd,
  position,
  onAddHandled,
}: Params): { addFiles: (paths: string[], targetTrack: string | undefined, start: number) => Promise<void>; importError: boolean } {
  const api = useApi();
  const [importError, setImportError] = useState(false);
  const consumedAdd = useRef<string | null>(null);

  const addFiles = useCallback(async (paths: string[], targetTrack: string | undefined, start: number) => {
    setImportError(false);
    try {
      const files = await Promise.all(paths.map(async (source) => {
        const info = await api.get<{
          duration: number;
          kind: 'audio' | 'video' | 'image';
          has_audio: boolean;
        }>(`/fs/info?path=${encodeURIComponent(source)}`);
        if (!Number.isFinite(info.duration) || info.duration <= 0) throw new Error('invalid duration');
        return { source, ...info };
      }));
      for (const operation of buildImportOperations(files, tracks, trackCount, targetTrack, start)) applyOp(operation);
    } catch {
      setImportError(true);
    }
  }, [api, applyOp, trackCount, tracks]);

  useEffect(() => {
    if (pendingAdd.length === 0) {
      consumedAdd.current = null;
      return;
    }
    const key = JSON.stringify(pendingAdd);
    if (consumedAdd.current === key) return;
    consumedAdd.current = key;
    void addFiles(pendingAdd, undefined, position).finally(() => onAddHandled?.());
  }, [addFiles, onAddHandled, pendingAdd, position]);

  return { addFiles, importError };
}

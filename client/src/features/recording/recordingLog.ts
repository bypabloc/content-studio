import { useCallback, useEffect, useRef } from 'react';
import { useApi } from '@/shared/api/context';
import { useSetting } from '@/shared/hooks/useSetting';

/** Ajuste del registro del micrófono. Apagado por defecto: sin él no se escribe nada (spec 010, D-7). */
export const RECORDING_LOG = 'diagnostics.recording_log';

export type RecordingLog = (event: string, detail?: Record<string, unknown>) => void;

/**
 * Anota un evento de la grabación o del micrófono en `logs/recording`. Con el ajuste apagado no hace nada y no llama a la API.
 * Un fallo al anotar no corta la grabación.
 */
export function useRecordingLog(): RecordingLog {
  const api = useApi();
  const [enabled] = useSetting(RECORDING_LOG, false);
  // La referencia deja la función estable: los efectos que la usan no se repiten cuando cambia el ajuste.
  const on = useRef(enabled);
  useEffect(() => {
    on.current = enabled;
  });
  return useCallback<RecordingLog>(
    (event, detail = {}) => {
      if (!on.current) return;
      api.post('/diagnostics/recording', { event, detail }).catch(() => undefined);
    },
    [api],
  );
}

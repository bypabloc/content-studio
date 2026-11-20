import { useQuery } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';

/** Lo que mide el server de un audio de out/ (`GET /media/info`): duración en segundos, LUFS y pico real en dB. */
export interface MediaInfo {
  duration: number;
  lufs: number;
  true_peak: number;
}

/** La duración, el LUFS y el pico de un audio. Sin ruta no pide nada. */
export function useMediaInfo(path: string) {
  const api = useApi();
  return useQuery({
    queryKey: ['media', 'info', path],
    queryFn: () => api.get<MediaInfo>(`/media/info?path=${encodeURIComponent(path)}`),
    enabled: path !== '',
  });
}

/** Los `n` picos (entre 0 y 1) de la forma de onda. Sin ruta no pide nada. */
export function useMediaPeaks(path: string, n = 2000) {
  const api = useApi();
  return useQuery({
    queryKey: ['media', 'peaks', path, n],
    queryFn: () => api.get<{ peaks: number[] }>(`/media/peaks?path=${encodeURIComponent(path)}&n=${n}`),
    enabled: path !== '',
  });
}

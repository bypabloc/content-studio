import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import { hashParams } from '@/shared/navigation/hash';

/**
 * La duración que pide Mezcla con «Generar música para esta voz» (spec 016, D-4): `#/music?match=<archivo>&tail=<s>`
 * iguala a la duración del archivo más la cola (intro + outro). Es `null` si la URL no trae `match`.
 */
export function useMatchDuration(): number | null {
  const api = useApi();
  const params = hashParams();
  const path = params.get('match');
  const tail = Number(params.get('tail') ?? 0);
  const info = useQuery({
    queryKey: ['music', 'match-path', path],
    queryFn: () => api.get<{ duration: number }>(`/media/info?path=${encodeURIComponent(path ?? '')}`),
    enabled: path !== null,
  });
  return info.data ? info.data.duration + tail : null;
}

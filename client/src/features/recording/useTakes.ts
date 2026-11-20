import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';

// Todo lo de voces vive bajo esta clave: una toma nueva refresca la lista del estilo, su veredicto y el perfil.
const VOICES = ['voices'];

/** El veredicto de una toma (`<n>.check.json`): `ok` o `retake`, con las razones y las notas como códigos del catálogo. */
export interface Check {
  verdict: 'ok' | 'retake';
  reasons: string[];
  notes: string[];
  messages: string[];
  measures: Record<string, number | number[]>;
}

/** Una toma con su ruta para reproducirla y su chequeo, si el trabajo ya corrió (`GET .../takes/{style}/{n}`). */
export interface TakeDetail {
  take: number;
  path: string | null;
  check: Check | null;
}

/** Las tomas de un estilo, por número (`GET .../takes/{style}`). */
export function useStyleTakes(slug: string, style: string) {
  const api = useApi();
  return useQuery({
    queryKey: [...VOICES, 'takes', slug, style],
    queryFn: () => api.get<{ style: string; takes: number[] }>(`/voices/profiles/${encodeURIComponent(slug)}/takes/${style}`),
  });
}

/** Una toma. Mientras el chequeo no está, se vuelve a pedir: el trabajo corre en la cola. */
export function useTakeDetail(slug: string, style: string, take: number) {
  const api = useApi();
  return useQuery({
    queryKey: [...VOICES, 'take', slug, style, take],
    queryFn: () => api.get<TakeDetail>(`/voices/profiles/${encodeURIComponent(slug)}/takes/${style}/${take}`),
    refetchInterval: (query) => (query.state.data?.check ? false : 1500),
  });
}

/** Sube el WAV de la grabación como la siguiente toma del estilo; el server encola su chequeo. */
export function useUploadTake(slug: string, style: string) {
  const api = useApi();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (wav: Uint8Array) =>
      api.upload<{ style: string; take: number; job: number }>(
        `/voices/profiles/${encodeURIComponent(slug)}/takes/${style}`,
        wav,
        'audio/wav',
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: VOICES }),
  });
}

/** Elige una toma: se copia a la referencia del estilo, y la anterior pasa a las tomas. */
export function useChooseTake(slug: string, style: string) {
  const api = useApi();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (take: number) => api.post(`/voices/profiles/${encodeURIComponent(slug)}/takes/${style}/${take}/choose`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: VOICES }),
  });
}

/** Borra una toma: va a la papelera del perfil y la referencia elegida no cambia (`DELETE .../takes/{style}/{n}`). */
export function useDeleteTake(slug: string, style: string) {
  const api = useApi();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (take: number) => api.del(`/voices/profiles/${encodeURIComponent(slug)}/takes/${style}/${take}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: VOICES }),
  });
}

/** Importa un tramo de un audio o video como toma del estilo, con el permiso del dueño; el server encola su chequeo. */
/** La duración y los picos del origen que se va a importar, para marcar el tramo sobre su onda (spec 010, D-4). */
export function useSourcePeaks(path: string) {
  const api = useApi();
  return useQuery({
    queryKey: [...VOICES, 'import-peaks', path],
    queryFn: () =>
      api.get<{ duration: number; peaks: number[] }>(`/voices/import/peaks?path=${encodeURIComponent(path)}&n=800`),
    enabled: path !== '',
  });
}

export function useImportSpan(slug: string) {
  const api = useApi();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (span: { path: string; start: number; end: number; style: string }) =>
      api.post<{ style: string; take: number; job: number }>(`/voices/profiles/${encodeURIComponent(slug)}/import`, {
        ...span,
        consent: true,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: VOICES }),
  });
}

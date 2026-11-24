import { useQuery } from '@tanstack/react-query';

import { useApi } from '@/shared/api/context';
import { hashParams } from '@/shared/navigation/hash';

/** Un trabajo con los parámetros que lo crearon. */
export interface SourceJob {
  id: number;
  kind: string;
  params: Record<string, unknown>;
}

/**
 * «Editar y repetir» de la Biblioteca (spec 020, D-4): la sección abre con `?from_job=<id>` y carga de entrada los parámetros
 * de ese trabajo. Devuelve el trabajo cuando llega, o null sin `from_job`. La sección aplica sus campos una sola vez.
 */
export function useFromJob(): SourceJob | null {
  const api = useApi();
  const raw = hashParams().get('from_job');
  const id = raw && /^\d+$/.test(raw) ? Number(raw) : null;
  const job = useQuery({
    queryKey: ['jobs', id],
    queryFn: () => api.get<SourceJob>(`/jobs/${id}`),
    enabled: id !== null,
  });
  return id !== null && job.data ? job.data : null;
}

/** Un parámetro de texto del trabajo, o el valor por defecto si falta o no es texto. */
export function textParam(job: SourceJob, key: string, fallback = ''): string {
  const value = job.params[key];
  return typeof value === 'string' ? value : fallback;
}

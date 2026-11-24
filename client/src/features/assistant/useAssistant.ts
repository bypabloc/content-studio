import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';

type Job = components['schemas']['Job'];
export type LlmStatus = components['schemas']['LlmStatus'];

const FINISHED = ['done', 'error', 'cancelled'];

/** El estado del asistente (spec 021, D-5). Mientras hay un modelo caliente se refresca, para la cuenta regresiva. */
export function useAssistantStatus() {
  const api = useApi();
  return useQuery({
    queryKey: ['llm', 'status'],
    queryFn: () => api.get<LlmStatus>('/llm/status'),
    refetchInterval: (query) => (query.state.data?.loaded ? 5000 : false),
  });
}

/** ¿Están el runtime y el modelo elegido en disco? Sin ellos, los botones llevan a Motores. */
export function assistantReady(status: LlmStatus | undefined): boolean {
  return Boolean(status?.runtime_installed && status.models.some((model) => model.model === status.selected && model.installed));
}

/**
 * Una tarea del asistente (`llm.<tarea>`): la encola, sigue su trabajo en la caché de la cola (que actualizan los eventos)
 * y, cuando termina, pide su propuesta. Nada se aplica aquí: lo decide la pantalla con lo que el usuario acepta.
 */
export function useAssistantTask<R>(kind: string) {
  const api = useApi();
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<number | null>(null);
  const start = useMutation({
    mutationFn: (params: Record<string, unknown>) => api.post<Job>('/jobs', { kind, params }),
    onSuccess: (job) => {
      setJobId(job.id);
      void queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: () => api.get<Job[]>('/jobs'), enabled: jobId !== null });
  const job = jobs.data?.find((item) => item.id === jobId);
  const result = useQuery({
    queryKey: ['llm', 'result', jobId],
    queryFn: () => api.get<R>(`/llm/jobs/${jobId}/result`),
    enabled: job?.status === 'done',
  });
  const busy = start.isPending || (jobId !== null && !FINISHED.includes(job?.status ?? 'queued'));
  return {
    run: (params: Record<string, unknown>) => {
      setJobId(null);
      start.mutate(params);
    },
    busy,
    jobId,
    error: job?.status === 'error' ? (job.error_code ?? 'process_failed') : start.error ? 'process_failed' : null,
    result: job?.status === 'done' ? result.data : undefined,
    reset: () => setJobId(null),
  };
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useApi } from '@/shared/api/context';
import { sortedBy, type Job, type QueueState } from '@/shared/api/events';
import { t } from '@/shared/i18n/t';

/** La cola: los trabajos (los actualiza SSE), la pausa y las acciones de cada trabajo y de la cola. */
export function useQueue() {
  const api = useApi();
  const queryClient = useQueryClient();
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: () => api.get<Job[]>('/jobs') });
  const queue = useQuery({ queryKey: ['queue'], queryFn: () => api.get<QueueState>('/queue') });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['jobs'] });
  const cancel = useMutation({ mutationFn: (id: number) => api.post(`/jobs/${id}/cancel`), onSuccess: refresh });
  const retry = useMutation({ mutationFn: (id: number) => api.post(`/jobs/${id}/retry`), onSuccess: refresh });
  const pause = useMutation({
    mutationFn: (paused: boolean) => api.post<QueueState>(paused ? '/queue/pause' : '/queue/resume'),
    onSuccess: (state) => queryClient.setQueryData(['queue'], state),
  });
  // Si el server no acepta el orden, vuelve a su lista y avisa (el reordenado se mostró antes de mandarlo).
  const order = useMutation({
    mutationFn: (ids: number[]) => api.put('/queue/order', { ids }),
    onError: () => {
      void refresh();
      toast.error(t('queue.order_failed'));
    },
  });

  const paused = queue.data?.paused ?? false;
  return {
    jobs: jobs.data ?? [],
    paused,
    cancel: (id: number) => cancel.mutate(id),
    retry: (id: number) => retry.mutate(id),
    togglePause: () => pause.mutate(!paused),
    /** Muestra el orden nuevo enseguida y lo manda al server. */
    reorder: (ids: number[]) => {
      queryClient.setQueryData<Job[]>(['jobs'], (list) => (list ? sortedBy(list, ids) : list));
      order.mutate(ids);
    },
  };
}

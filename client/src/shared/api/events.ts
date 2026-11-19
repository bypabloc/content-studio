import type { QueryClient } from '@tanstack/react-query';
import type { Connection } from './client';
import type { components } from './schema';

export type Job = components['schemas']['Job'];
export type QueueState = components['schemas']['QueueState'];

/** El evento `queue` trae el estado de la pausa, o el orden nuevo de los trabajos al reordenar. */
type QueueEvent = QueueState | { order: number[] };

export interface EventSourceLike {
  addEventListener(type: string, listener: (event: MessageEvent<string>) => void): void;
  close(): void;
}

/**
 * Un único EventSource a /events: cada evento actualiza la caché de TanStack Query, sin volver a pedir los datos.
 * Devuelve la función que cierra la conexión.
 */
export function connectEvents(
  connection: Connection,
  queryClient: QueryClient,
  open: (url: string) => EventSourceLike = (url) => new EventSource(url),
): () => void {
  const source = open(`${connection.baseUrl}/events?token=${encodeURIComponent(connection.token)}`);

  source.addEventListener('job', (event) => {
    const changed = JSON.parse(event.data) as Job;
    queryClient.setQueryData(['jobs', changed.id], changed);
    // Si la lista no se pidió todavía, el updater devuelve undefined y la caché no cambia.
    queryClient.setQueryData<Job[]>(['jobs'], (jobs) => (jobs ? upsert(jobs, changed) : jobs));
  });

  source.addEventListener('queue', (event) => {
    const data = JSON.parse(event.data) as QueueEvent;
    if ('order' in data) {
      queryClient.setQueryData<Job[]>(['jobs'], (jobs) => (jobs ? sortedBy(jobs, data.order) : jobs));
    } else {
      queryClient.setQueryData<QueueState>(['queue'], data);
    }
  });

  return () => source.close();
}

function upsert(jobs: Job[], changed: Job): Job[] {
  return jobs.some((job) => job.id === changed.id)
    ? jobs.map((job) => (job.id === changed.id ? changed : job))
    : [...jobs, changed];
}

function sortedBy(jobs: Job[], order: number[]): Job[] {
  const rank = new Map(order.map((id, index) => [id, index]));
  return [...jobs].sort((a, b) => (rank.get(a.id) ?? order.length) - (rank.get(b.id) ?? order.length));
}

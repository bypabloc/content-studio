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

export interface EventsOptions {
  /** Abre la conexión; por defecto, el EventSource del navegador (Tauri usa el de su webview). */
  open?: (url: string) => EventSourceLike;
  /** Se llama una vez por trabajo cuando pasa a `done` o `error`: ahí van los avisos. */
  onFinished?: (job: Job) => void;
}

/**
 * Un único EventSource a /events: cada evento actualiza la caché de TanStack Query, sin volver a pedir los datos.
 * Devuelve la función que cierra la conexión.
 */
export function connectEvents(connection: Connection, queryClient: QueryClient, options: EventsOptions = {}): () => void {
  const open = options.open ?? ((url: string) => new EventSource(url));
  const source = open(`${connection.baseUrl}/events?token=${encodeURIComponent(connection.token)}`);

  source.addEventListener('job', (event) => {
    const changed = JSON.parse(event.data) as Job;
    const before = queryClient.getQueryData<Job[]>(['jobs'])?.find((job) => job.id === changed.id)?.status;
    queryClient.setQueryData(['jobs', changed.id], changed);
    // Si la lista no se pidió todavía, el updater devuelve undefined y la caché no cambia.
    queryClient.setQueryData<Job[]>(['jobs'], (jobs) => (jobs ? upsert(jobs, changed) : jobs));
    const finished = changed.status === 'done' || changed.status === 'error';
    if (finished && before !== changed.status) options.onFinished?.(changed);
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

/**
 * Reordena solo los trabajos que trae `order` (los en espera): ocupan los mismos lugares y cambian entre ellos. Los
 * demás (en curso, con error o terminados) se quedan donde estaban.
 */
export function sortedBy(jobs: Job[], order: number[]): Job[] {
  const rank = new Map(order.map((id, index) => [id, index]));
  const listed = jobs.filter((job) => rank.has(job.id)).sort((a, b) => (rank.get(a.id) ?? 0) - (rank.get(b.id) ?? 0));
  let next = 0;
  return jobs.map((job) => (rank.has(job.id) ? listed[next++] : job));
}

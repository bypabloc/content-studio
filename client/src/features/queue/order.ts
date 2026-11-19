import type { Job } from '@/shared/api/events';

/**
 * El orden de los trabajos en espera (los ids) con `activeId` movido a la posición de `overId`. Un trabajo que
 * no está en espera no se mueve: devuelve el orden actual.
 */
export function moveQueued(jobs: readonly Job[], activeId: number, overId: number): number[] {
  const queued = jobs.filter((job) => job.status === 'queued').map((job) => job.id);
  const from = queued.indexOf(activeId);
  const to = queued.indexOf(overId);
  if (from < 0 || to < 0) return queued;
  const next = [...queued];
  next.splice(from, 1);
  next.splice(to, 0, activeId);
  return next;
}

/** El orden nuevo tras soltar un trabajo sobre otro, o null si no cambió nada (sin destino o el mismo). */
export function dropOrder(jobs: readonly Job[], activeId: number, overId: number | null): number[] | null {
  if (overId === null || overId === activeId) return null;
  return moveQueued(jobs, activeId, overId);
}

import { describe, expect, it } from 'vitest';
import { dropOrder, moveQueued } from '@/features/queue/order';
import type { Job } from '@/shared/api/events';

function job(id: number, status: Job['status']): Job {
  return {
    id,
    kind: 'music',
    resource: 'gpu',
    status,
    position: id,
    params: {},
    progress: 0,
    created_at: '2026-11-19T10:00:00Z',
  };
}

describe('moveQueued', () => {
  const jobs = [job(1, 'running'), job(2, 'queued'), job(3, 'queued'), job(4, 'queued')];

  it('mueve un trabajo en espera a la posición de otro en espera', () => {
    expect(moveQueued(jobs, 4, 2)).toEqual([4, 2, 3]);
  });

  it('un trabajo en curso no se mueve: devuelve el orden de espera tal cual', () => {
    expect(moveQueued(jobs, 1, 2)).toEqual([2, 3, 4]);
  });

  it('dropOrder: soltar sin destino o sobre sí mismo no cambia nada', () => {
    expect(dropOrder(jobs, 4, null)).toBeNull();
    expect(dropOrder(jobs, 4, 4)).toBeNull();
    expect(dropOrder(jobs, 4, 2)).toEqual([4, 2, 3]);
  });
});

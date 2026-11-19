import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it } from 'vitest';
import { connectEvents, type EventSourceLike, type Job } from '@/shared/api/events';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function job(id: number, patch: Partial<Job> = {}): Job {
  return {
    id,
    kind: 'music',
    resource: 'gpu',
    status: 'queued',
    position: id,
    params: {},
    progress: 0,
    created_at: '2026-11-19T10:00:00Z',
    ...patch,
  };
}

// Un EventSource simulado: el test dispara los eventos a mano.
class FakeSource implements EventSourceLike {
  readonly listeners = new Map<string, (event: MessageEvent<string>) => void>();
  url = '';
  closed = false;

  addEventListener(type: string, listener: (event: MessageEvent<string>) => void): void {
    this.listeners.set(type, listener);
  }

  close(): void {
    this.closed = true;
  }

  emit(type: string, data: unknown): void {
    this.listeners.get(type)?.({ data: JSON.stringify(data) } as MessageEvent<string>);
  }
}

function setup() {
  const queryClient = new QueryClient();
  const source = new FakeSource();
  const disconnect = connectEvents(connection, queryClient, (url) => {
    source.url = url;
    return source;
  });
  return { queryClient, source, disconnect };
}

describe('connectEvents', () => {
  it('abre un solo EventSource con el token en la URL', () => {
    const { source } = setup();

    expect(source.url).toBe('http://127.0.0.1:9000/events?token=tok');
  });

  it('un evento job actualiza la lista y el trabajo sin pedirlos otra vez', () => {
    const { queryClient, source } = setup();
    queryClient.setQueryData(['jobs'], [job(1), job(2)]);

    source.emit('job', job(1, { status: 'running', progress: 0.4 }));

    expect(queryClient.getQueryData<Job[]>(['jobs'])?.map((item) => item.progress)).toEqual([0.4, 0]);
    expect(queryClient.getQueryData<Job>(['jobs', 1])?.progress).toBe(0.4);
  });

  it('un evento job no crea la lista si todavía no se pidió', () => {
    const { queryClient, source } = setup();

    source.emit('job', job(1));

    expect(queryClient.getQueryData(['jobs'])).toBeUndefined();
  });

  it('un evento queue con paused guarda el estado de la cola', () => {
    const { queryClient, source } = setup();

    source.emit('queue', { paused: true });

    expect(queryClient.getQueryData(['queue'])).toEqual({ paused: true });
  });

  it('un evento queue con order reordena la lista cacheada', () => {
    const { queryClient, source } = setup();
    queryClient.setQueryData(['jobs'], [job(1), job(2), job(3)]);

    source.emit('queue', { order: [3, 1, 2] });

    expect(queryClient.getQueryData<Job[]>(['jobs'])?.map((item) => item.id)).toEqual([3, 1, 2]);
  });

  it('un trabajo que no está en el orden nuevo va al final', () => {
    const { queryClient, source } = setup();
    queryClient.setQueryData(['jobs'], [job(1), job(2), job(9)]);

    source.emit('queue', { order: [2, 1] });

    expect(queryClient.getQueryData<Job[]>(['jobs'])?.map((item) => item.id)).toEqual([2, 1, 9]);
  });

  it('un evento queue con order no crea la lista si todavía no se pidió', () => {
    const { queryClient, source } = setup();

    source.emit('queue', { order: [1] });

    expect(queryClient.getQueryData(['jobs'])).toBeUndefined();
  });

  it('desconectar cierra el EventSource', () => {
    const { source, disconnect } = setup();

    disconnect();

    expect(source.closed).toBe(true);
  });
});

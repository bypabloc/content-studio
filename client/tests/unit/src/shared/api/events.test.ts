import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';
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

function setup(onFinished?: (job: Job) => void) {
  const queryClient = new QueryClient();
  const source = new FakeSource();
  const disconnect = connectEvents(connection, queryClient, {
    open: (url) => {
      source.url = url;
      return source;
    },
    onFinished,
  });
  return { queryClient, source, disconnect };
}

describe('avisos de trabajos terminados', () => {
  it('avisa una vez cuando un trabajo pasa a done, y no otra vez con el mismo estado', () => {
    const onFinished = vi.fn();
    const { queryClient, source } = setup(onFinished);
    queryClient.setQueryData(['jobs'], [job(1, { status: 'running' })]);

    source.emit('job', job(1, { status: 'done', progress: 1 }));
    source.emit('job', job(1, { status: 'done', progress: 1 }));

    expect(onFinished).toHaveBeenCalledTimes(1);
    expect(onFinished).toHaveBeenCalledWith(expect.objectContaining({ id: 1, status: 'done' }));
  });

  it('un trabajo que pasa a error también avisa; uno en curso no', () => {
    const onFinished = vi.fn();
    const { source } = setup(onFinished);

    source.emit('job', job(2, { status: 'running' }));
    source.emit('job', job(2, { status: 'error' }));

    expect(onFinished).toHaveBeenCalledTimes(1);
    expect(onFinished).toHaveBeenCalledWith(expect.objectContaining({ id: 2, status: 'error' }));
  });
});

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

  it('un trabajo que no está en el orden nuevo (en curso o con error) se queda en su lugar', () => {
    const { queryClient, source } = setup();
    queryClient.setQueryData(['jobs'], [job(1), job(9), job(2)]);

    source.emit('queue', { order: [2, 1] });

    expect(queryClient.getQueryData<Job[]>(['jobs'])?.map((item) => item.id)).toEqual([2, 9, 1]);
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

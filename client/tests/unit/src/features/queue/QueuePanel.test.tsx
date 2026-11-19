import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { QueuePanel } from '@/features/queue/QueuePanel';
import { ApiProvider } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

// El DndContext real, pero con la función de soltar guardada para dispararla desde el test.
const { drop } = vi.hoisted(() => ({ drop: { onDragEnd: null as null | ((event: unknown) => void) } }));
vi.mock('@dnd-kit/core', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@dnd-kit/core')>();
  return {
    ...actual,
    DndContext: (props: Parameters<typeof actual.DndContext>[0]) => {
      drop.onDragEnd = props.onDragEnd as typeof drop.onDragEnd;
      return <actual.DndContext {...props} />;
    },
  };
});

// El aviso de error del reordenado: el test comprueba la llamada, sin pintar el toast.
const { toastError } = vi.hoisted(() => ({ toastError: vi.fn() }));
vi.mock('sonner', () => ({ toast: { error: toastError, success: vi.fn() } }));

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

// El EventSource que abre ApiProvider: el test emite a mano los eventos que mandaría el server (AC-5 y AC-6).
class FakeEvents {
  static last: FakeEvents;
  readonly listeners = new Map<string, (event: MessageEvent<string>) => void>();

  constructor() {
    FakeEvents.last = this;
  }

  addEventListener(type: string, listener: (event: MessageEvent<string>) => void): void {
    this.listeners.set(type, listener);
  }

  close(): void {
    this.listeners.clear();
  }

  emit(type: string, data: unknown): void {
    this.listeners.get(type)?.({ data: JSON.stringify(data) } as MessageEvent<string>);
  }
}

function job(id: number, status: 'queued' | 'running' | 'error', patch: Record<string, unknown> = {}) {
  return {
    id,
    kind: 'music',
    resource: 'gpu',
    status,
    position: id,
    params: {},
    progress: 0,
    created_at: '2026-11-19T10:00:00Z',
    ...patch,
  };
}

// Respuestas por "MÉTODO /ruta"; cada llamada queda registrada para comprobar el endpoint.
function routes(table: Record<string, unknown>) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const key = `${init?.method ?? 'GET'} ${new URL(url).pathname}`;
    return new Response(JSON.stringify(table[key] ?? {}), { status: 200 });
  });
}

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>
        <QueuePanel />
      </ApiProvider>
    </QueryClientProvider>,
  );
}

// La fila de un trabajo cuando ya llegó la lista (waitFor vuelve a probar hasta que exista).
function rowOf(id: number): Promise<HTMLElement> {
  return waitFor(() => {
    const row = document.querySelector<HTMLElement>(`[data-job="${id}"]`);
    if (row === null) throw new Error(`no row for job ${id}`);
    return row;
  });
}

const calls = (fetchMock: ReturnType<typeof routes>) =>
  fetchMock.mock.calls.map(([url, init]) => `${init?.method ?? 'GET'} ${new URL(url as string).pathname}`);

const idsOnScreen = () => [...document.querySelectorAll<HTMLElement>('[data-job]')].map((row) => row.dataset.job);

describe('QueuePanel', () => {
  let fetchMock: ReturnType<typeof routes>;

  beforeEach(() => {
    fetchMock = routes({
      'GET /jobs': [
        job(1, 'running', { progress: 0.4, stage: 'mezcla' }),
        job(2, 'queued'),
        job(3, 'error'),
        job(4, 'queued'),
      ],
      'GET /queue': { paused: false },
      'POST /jobs/2/cancel': { cancelled: true },
      'POST /jobs/3/retry': job(4, 'queued'),
      'POST /queue/pause': { paused: true },
    });
    vi.stubGlobal('fetch', fetchMock);
    vi.stubGlobal('EventSource', FakeEvents);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('el trabajo en curso muestra su progreso y su etapa', async () => {
    renderPanel();

    expect(await screen.findByText(t('queue.progress', { percent: 40 }))).toBeTruthy();
    expect(screen.getByText('mezcla')).toBeTruthy();
  });

  it('un evento job de SSE actualiza la fila sin pedir la lista otra vez (AC-5)', async () => {
    renderPanel();
    await rowOf(1);
    const listRequests = calls(fetchMock).filter((call) => call === 'GET /jobs').length;

    act(() => FakeEvents.last.emit('job', job(1, 'running', { progress: 0.7, stage: 'masterizado' })));

    expect(await screen.findByText(t('queue.progress', { percent: 70 }))).toBeTruthy();
    expect(screen.getByText('masterizado')).toBeTruthy();
    expect(calls(fetchMock).filter((call) => call === 'GET /jobs')).toHaveLength(listRequests);
  });

  it('un evento queue con el orden nuevo reordena las filas en pantalla (AC-6)', async () => {
    renderPanel();
    await rowOf(2);

    act(() => FakeEvents.last.emit('queue', { order: [4, 2] }));

    // Solo cambian entre sí los dos en espera (2 y 4); el 1 (en curso) y el 3 (con error) se quedan donde estaban.
    await waitFor(() => expect(idsOnScreen()).toEqual(['1', '4', '3', '2']));
  });

  it('cancelar un trabajo en espera llama a su endpoint', async () => {
    renderPanel();
    const row = await rowOf(2);

    fireEvent.click(within(row).getByRole('button', { name: t('queue.cancel') }));

    await waitFor(() => expect(calls(fetchMock)).toContain('POST /jobs/2/cancel'));
  });

  it('reintentar un trabajo con error llama a su endpoint', async () => {
    renderPanel();
    const row = await rowOf(3);

    fireEvent.click(within(row).getByRole('button', { name: t('queue.retry') }));

    await waitFor(() => expect(calls(fetchMock)).toContain('POST /jobs/3/retry'));
  });

  it('soltar un trabajo en espera sobre otro reordena la cola en el server', async () => {
    renderPanel();
    await rowOf(2);

    drop.onDragEnd?.({ active: { id: 2 }, over: { id: 4 } });

    // Con dos trabajos en espera (2 y 4) el orden cambia: el 2 pasa a la posición del 4.
    await waitFor(() => expect(calls(fetchMock)).toContain('PUT /queue/order'));
    const put = fetchMock.mock.calls.find(([, init]) => init?.method === 'PUT');
    expect(JSON.parse(String(put?.[1]?.body))).toEqual({ ids: [4, 2] });
  });

  it('soltar fuera de la lista no pide ningún reordenado', async () => {
    renderPanel();
    await rowOf(2);

    drop.onDragEnd?.({ active: { id: 2 }, over: null });

    expect(calls(fetchMock)).not.toContain('PUT /queue/order');
  });

  it('si el server rechaza el orden, avisa y vuelve a la lista que tiene', async () => {
    const answer = fetchMock.getMockImplementation()!;
    fetchMock.mockImplementation(async (url: string, init?: RequestInit) =>
      init?.method === 'PUT' ? new Response('{}', { status: 500 }) : answer(url, init),
    );
    renderPanel();
    await rowOf(2);

    drop.onDragEnd?.({ active: { id: 2 }, over: { id: 4 } });

    await waitFor(() => expect(toastError).toHaveBeenCalledWith(t('queue.order_failed')));
    await waitFor(() => expect(idsOnScreen()).toEqual(['1', '2', '3', '4']));
  });

  it('sin trabajos muestra la cola vacía, y reanudar llama al endpoint', async () => {
    fetchMock = routes({ 'GET /jobs': [], 'GET /queue': { paused: true }, 'POST /queue/resume': { paused: false } });
    vi.stubGlobal('fetch', fetchMock);
    renderPanel();

    expect(await screen.findByText(t('queue.empty'))).toBeTruthy();
    fireEvent.click(await screen.findByRole('button', { name: t('queue.resume') }));

    await waitFor(() => expect(calls(fetchMock)).toContain('POST /queue/resume'));
  });

  it('pausar la cola llama al endpoint y el botón pasa a reanudar', async () => {
    renderPanel();

    fireEvent.click(await screen.findByRole('button', { name: t('queue.pause') }));

    expect(await screen.findByRole('button', { name: t('queue.resume') })).toBeTruthy();
    expect(calls(fetchMock)).toContain('POST /queue/pause');
  });

  it('la cola se pliega y se despliega con su botón (D-6)', async () => {
    renderPanel();
    await rowOf(2);

    fireEvent.click(screen.getByRole('button', { name: t('queue.collapse') }));
    expect(screen.queryByRole('list')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: t('queue.expand') }));
    expect(await rowOf(2)).toBeTruthy();
  });

  it('un trabajo de narración se muestra con su nombre en español, no con la clave del server', async () => {
    fetchMock = routes({ 'GET /jobs': [job(5, 'queued', { kind: 'narration' })], 'GET /queue': { paused: false } });
    vi.stubGlobal('fetch', fetchMock);
    renderPanel();

    expect(await screen.findByText(t('queue.kind.narration'))).toBeTruthy();
  });
});

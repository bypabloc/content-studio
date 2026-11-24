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

function job(id: number, status: 'queued' | 'running' | 'done' | 'error', patch: Record<string, unknown> = {}) {
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
    window.location.hash = '';
  });

  it('muestra el trabajo terminado más reciente y abre sus medios en el Editor', async () => {
    fetchMock = routes({
      'GET /jobs': [
        job(4, 'done', { output_dir: 'out/narration/4', finished_at: '2026-11-22T10:00:00Z' }),
        job(5, 'done', { output_dir: 'out/narration/5', finished_at: '2026-11-23T10:00:00Z' }),
      ],
      'GET /queue': { paused: false },
      'GET /fs/list': { entries: [{ path: 'out/narration/5/take.wav', kind: 'audio' }] },
    });
    vi.stubGlobal('fetch', fetchMock);
    renderPanel();
    const row = await rowOf(5);

    expect(screen.queryByText(t('queue.status.done'))).toBeTruthy();
    expect(document.querySelector('[data-job="4"]')).toBeNull();
    await within(row).findByRole('button', { name: 'Abrir en Editor' });
    fireEvent.click(within(row).getByRole('button', { name: 'Abrir en Editor' }));

    await waitFor(() => expect(new URLSearchParams(window.location.hash.split('?')[1]).getAll('add')).toEqual([
      'out/narration/5/take.wav',
    ]));
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

    fireEvent.click(within(row).getByRole('button', { name: t('action.cancel') }));

    await waitFor(() => expect(calls(fetchMock)).toContain('POST /jobs/2/cancel'));
  });

  it('reintentar un trabajo con error llama a su endpoint', async () => {
    renderPanel();
    const row = await rowOf(3);

    fireEvent.click(within(row).getByRole('button', { name: t('action.retry') }));

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
    fireEvent.click(await screen.findByRole('button', { name: t('action.resume') }));

    await waitFor(() => expect(calls(fetchMock)).toContain('POST /queue/resume'));
  });

  it('pausar la cola llama al endpoint y el botón pasa a reanudar', async () => {
    renderPanel();

    fireEvent.click(await screen.findByRole('button', { name: t('action.pause') }));

    expect(await screen.findByRole('button', { name: t('action.resume') })).toBeTruthy();
    expect(calls(fetchMock)).toContain('POST /queue/pause');
  });

  it('la cola se pliega y se despliega con su botón (D-6)', async () => {
    renderPanel();
    await rowOf(2);

    expect(screen.getByRole('button', { name: t('action.collapse') }).querySelector('svg')?.getAttribute('class')).toContain('lucide-chevron-down');
    fireEvent.click(screen.getByRole('button', { name: t('action.collapse') }));
    expect(screen.queryByRole('list')).toBeNull();
    expect(screen.getByRole('button', { name: t('action.expand') }).querySelector('svg')?.getAttribute('class')).toContain('lucide-chevron-up');

    fireEvent.click(screen.getByRole('button', { name: t('action.expand') }));
    expect(await rowOf(2)).toBeTruthy();
  });

  it('un trabajo de narración se muestra con su nombre en español, no con la clave del server', async () => {
    fetchMock = routes({ 'GET /jobs': [job(5, 'queued', { kind: 'narration' })], 'GET /queue': { paused: false } });
    vi.stubGlobal('fetch', fetchMock);
    renderPanel();

    expect(await screen.findByText(t('queue.kind.narration'))).toBeTruthy();
  });

  it('WHEN a waiting job is shown THEN cancel and drag are icon buttons named by the catalog (spec 009, D-4)', async () => {
    renderPanel();
    const row = await rowOf(2);

    for (const [name, icon] of [
      [t('action.cancel'), 'lucide-circle-x'],
      [t('action.drag'), 'lucide-grip-vertical'],
    ] as const) {
      const button = within(row).getByRole('button', { name });
      expect(button.textContent).toBe('');
      expect(button.querySelector('svg')?.getAttribute('class')).toContain(icon);
    }
  });

  it('WHEN a job with error is shown THEN retry is an icon button named by the catalog (spec 009, D-4)', async () => {
    renderPanel();
    const row = await rowOf(3);

    const button = within(row).getByRole('button', { name: t('action.retry') });
    expect(button.textContent).toBe('');
    expect(button.querySelector('svg')?.getAttribute('class')).toContain('lucide-rotate-cw');
  });

  it('WHEN each job state is shown THEN its status has an icon (spec 009, D-5)', async () => {
    renderPanel();
    const running = await rowOf(1);
    const waiting = await rowOf(2);
    const failed = await rowOf(3);

    expect(running.querySelector('svg.lucide-loader-circle.animate-spin')).not.toBeNull();
    expect(waiting.querySelector('svg.lucide-clock')).not.toBeNull();
    expect(failed.querySelector('svg.lucide-circle-alert')).not.toBeNull();
  });

  it('WHEN the queue shows its pause and fold buttons THEN they are icon buttons named by the catalog (spec 009, D-4)', async () => {
    renderPanel();
    await rowOf(2);

    const pause = screen.getByRole('button', { name: t('action.pause') });
    expect(pause.textContent).toBe('');
    expect(pause.querySelector('svg')?.getAttribute('class')).toContain('lucide-pause');
    expect(screen.getByRole('button', { name: t('action.collapse') }).textContent).toBe('');
  });
});

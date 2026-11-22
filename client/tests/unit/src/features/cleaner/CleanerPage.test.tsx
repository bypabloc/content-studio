import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CleanerPage } from '@/features/cleaner/CleanerPage';
import { t } from '@/shared/i18n/t';

const { api, review } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  review: { jobId: null as number | null },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));
// La revisión tiene sus propias pruebas: aquí solo importa qué trabajo abre «Revisar».
vi.mock('@/features/cleaner/CleanReview', () => ({
  CleanReview: (props: { jobId: number }) => {
    review.jobId = props.jobId;
    return null;
  },
}));

const engines = [
  {
    engine: 'faster-whisper',
    models: [
      { model: 'small', size_gb: 0.5, vram_gb: 1, recommended: false, downloaded: false },
      { model: 'large-v3-turbo', size_gb: 1.6, vram_gb: 3, recommended: true, downloaded: true },
    ],
  },
];
const analysis = (overrides: Record<string, unknown>) => ({
  id: 7,
  kind: 'clean.analyze',
  status: 'done',
  progress: 1,
  stage: null,
  output_dir: 'out/clean/7',
  params: { input: '/media/a.mp4', auto_render: false },
  ...overrides,
});

let analyses: unknown[] = [];
let renders: unknown[] = [];

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <CleanerPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  analyses = [];
  renders = [];
  api.get.mockImplementation(async (path: string) => {
    if (path === '/engines') return engines;
    if (path === '/jobs?kind=clean.analyze') return analyses;
    if (path === '/jobs?kind=clean.render') return renders;
    if (path.startsWith('/settings/')) return { key: path.replace('/settings/', ''), value: null };
    return [];
  });
  api.post.mockImplementation(async (_path: string, body: { params: Record<string, unknown> }) => ({ id: 1, ...body }));
  vi.mocked(open).mockResolvedValue(['/media/a.mp4', '/media/b.wav']);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  review.jobId = null;
});

async function chooseFiles() {
  await userEvent.click(screen.getByRole('button', { name: t('cleaner.files.pick') }));
  await screen.findByText('b.wav');
}

describe('CleanerPage (spec 013, D-6)', () => {
  it('lote: Analizar encola un clean.analyze por archivo, sin auto_render, con el modelo y los márgenes', async () => {
    renderPage();
    await chooseFiles();

    await userEvent.click(screen.getByRole('button', { name: t('cleaner.analyze') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
    expect(api.post).toHaveBeenCalledWith('/jobs', {
      kind: 'clean.analyze',
      params: {
        input: '/media/a.mp4',
        model: 'large-v3-turbo',
        language: 'es',
        min_gap: 0.5,
        padding: 0.15,
        edges: true,
        auto_render: false,
      },
    });
  }, 20_000);

  it('AC-8: «Aplicar todos sin revisar» encola los análisis con auto_render', async () => {
    renderPage();
    await chooseFiles();

    await userEvent.click(screen.getByRole('button', { name: t('cleaner.auto') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
    expect(api.post).toHaveBeenCalledWith('/jobs', expect.objectContaining({ params: expect.objectContaining({ auto_render: true }) }));
  });

  it('la lista muestra el estado de cada análisis; «Revisar» abre la revisión de ese trabajo', async () => {
    analyses = [analysis({ id: 7, params: { input: '/media/a.mp4', auto_render: false } })];
    renderPage();

    expect(await screen.findByText('a.mp4')).toBeTruthy();
    expect(screen.getByText(t('cleaner.status.review'))).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: t('cleaner.review') }));

    expect(review.jobId).toBe(7);
  });

  it('AC-8: un análisis con auto_render muestra «Renderizando» mientras su render corre', async () => {
    analyses = [analysis({ id: 8, output_dir: 'out/clean/8', params: { input: '/media/a.mp4', auto_render: true } })];
    renders = [{ id: 9, kind: 'clean.render', status: 'running', progress: 0.4, stage: 'render', params: { analysis: 'out/clean/8' } }];
    renderPage();

    expect(await screen.findByText(t('cleaner.status.rendering'))).toBeTruthy();
  });

  it('cada estado del lote tiene su texto: en cola, analizando, cancelado, listo y error (análisis o render)', async () => {
    analyses = [
      analysis({ id: 1, status: 'queued', progress: 0, output_dir: 'out/1', params: { input: '/media/q.mp4', auto_render: false } }),
      analysis({ id: 2, status: 'running', progress: 0.5, output_dir: 'out/2', params: { input: '/media/r.mp4', auto_render: false } }),
      analysis({ id: 3, status: 'error', output_dir: 'out/3', params: { input: '/media/e.mp4', auto_render: false } }),
      analysis({ id: 4, status: 'cancelled', output_dir: 'out/4', params: { input: '/media/c.mp4', auto_render: false } }),
      analysis({ id: 5, output_dir: 'out/5', params: { input: '/media/ok.mp4', auto_render: true } }),
      analysis({ id: 6, output_dir: 'out/6', params: { input: '/media/mal.mp4', auto_render: true } }),
    ];
    renders = [
      { id: 10, kind: 'clean.render', status: 'done', progress: 1, stage: null, params: { analysis: 'out/5' } },
      { id: 11, kind: 'clean.render', status: 'error', progress: 0, stage: null, params: { analysis: 'out/6' } },
    ];
    renderPage();

    expect(await screen.findByText(t('cleaner.status.queued'))).toBeTruthy();
    expect(screen.getByText(t('cleaner.status.running', { percent: 50 }))).toBeTruthy();
    expect(screen.getByText(t('cleaner.status.cancelled'))).toBeTruthy();
    expect(screen.getByText(t('cleaner.status.done'))).toBeTruthy();
    expect(screen.getAllByText(t('cleaner.status.error'))).toHaveLength(2);
  });

  it('si el servidor rechaza el envío, muestra su motivo y el lote no cambia (AC-9, formato no soportado)', async () => {
    api.post.mockRejectedValueOnce(new Error('a.txt no es un formato de audio o video que acepte el limpiador.'));
    renderPage();
    await chooseFiles();

    await userEvent.click(screen.getByRole('button', { name: t('cleaner.analyze') }));

    expect((await screen.findByRole('alert')).textContent).toContain('no es un formato de audio o video');
    expect(screen.getByText(t('cleaner.batch.empty'))).toBeTruthy();
  });

  it('elegir archivos: cancelar no agrega nada, una sola ruta cuenta, y analizar espera a tener archivos', async () => {
    vi.mocked(open).mockResolvedValueOnce(null);
    renderPage();
    const analyze = screen.getByRole('button', { name: t('cleaner.analyze') }) as HTMLButtonElement;
    expect(analyze.disabled).toBe(true);

    await userEvent.click(screen.getByRole('button', { name: t('cleaner.files.pick') }));
    expect(screen.getByText(t('cleaner.files.empty'))).toBeTruthy();

    vi.mocked(open).mockResolvedValueOnce('/media/solo.mp4');
    await userEvent.click(screen.getByRole('button', { name: t('cleaner.files.pick') }));
    await screen.findByText('solo.mp4');
    expect(analyze.disabled).toBe(false);
  });

  it('los márgenes y el interruptor de bordes van al análisis', async () => {
    renderPage();
    await chooseFiles();

    const gap = screen.getByRole('spinbutton', { name: t('cleaner.options.min_gap') });
    await userEvent.clear(gap);
    await userEvent.type(gap, '800');
    const padding = screen.getByRole('spinbutton', { name: t('cleaner.options.padding') });
    await userEvent.clear(padding);
    await userEvent.type(padding, '200');
    await userEvent.click(screen.getByRole('switch', { name: t('cleaner.options.edges') }));
    await userEvent.click(screen.getByRole('button', { name: t('cleaner.analyze') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
    expect(api.post).toHaveBeenCalledWith(
      '/jobs',
      expect.objectContaining({ params: expect.objectContaining({ min_gap: 0.8, padding: 0.2, edges: false }) }),
    );
  });
});

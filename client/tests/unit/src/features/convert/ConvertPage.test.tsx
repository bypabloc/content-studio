import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ConvertPage } from '@/features/convert/ConvertPage';
import { t } from '@/shared/i18n/t';
import { open } from '@tauri-apps/plugin-dialog';
import { openPath } from '@tauri-apps/plugin-opener';

const { api, drag } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    del: vi.fn(),
    fileUrl: (path: string) => `file://${path}`,
    queryUrl: (path: string) => `http://test${path}`,
  },
  drag: { handler: null as null | ((event: { payload: unknown }) => void) },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/api/webview', () => ({
  getCurrentWebview: () => ({
    onDragDropEvent: (handler: (event: { payload: unknown }) => void) => {
      drag.handler = handler;
      return Promise.resolve(() => {});
    },
  }),
}));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath: vi.fn() }));

const catalog = {
  formats: [
    { id: 'mp3', kind: 'audio' },
    { id: 'wav', kind: 'audio' },
    { id: 'mp4-h264', kind: 'video' },
  ],
  presets: [{ id: 'reels', width: 1080, height: 1920, fps: 30, reframe: 'center', recommended: true }],
};

let jobs: unknown[] = [];
let created: { kind: string; params: Record<string, unknown> }[] = [];

function job(overrides: Record<string, unknown>) {
  return {
    id: 1,
    kind: 'media.convert',
    status: 'queued',
    progress: 0,
    stage: null,
    output_dir: 'out/convert/1',
    params: { input: '/media/a.wav', target: 'mp3' },
    error_code: null,
    error_detail: null,
    ...overrides,
  };
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ConvertPage />
    </QueryClientProvider>,
  );
}

function drop(paths: string[]) {
  return act(async () => {
    drag.handler?.({ payload: { type: 'drop', paths } });
  });
}

beforeEach(() => {
  (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__ = {};
  jobs = [];
  created = [];
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/catalog/media')) return catalog;
    if (path.startsWith('/media/info')) return { duration: 1, lufs: -16, true_peak: -1, width: null, height: null };
    if (path === '/jobs?kind=media.convert') return jobs;
    if (path.startsWith('/settings/')) return { key: path, value: null };
    throw new Error(`GET inesperado: ${path}`);
  });
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({ key: path.replace('/settings/', ''), value: body.value }));
  api.post.mockImplementation(async (path: string, body: { kind: string; params: Record<string, unknown> }) => {
    if (path === '/jobs') {
      created.push(body);
      return job({ id: created.length, params: body.params });
    }
    if (path.endsWith('/cancel') || path.endsWith('/retry')) return {};
    throw new Error(`POST inesperado: ${path}`);
  });
});

afterEach(() => {
  delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
  cleanup();
  api.get.mockReset();
  api.put.mockReset();
  api.post.mockReset();
});

describe('ConvertPage', () => {
  it('AC-10: arrastrar 5 archivos y convertir a MP3 V2 encola 5 trabajos con esa calidad', async () => {
    renderPage();
    await drop(['/media/a.wav', '/media/b.wav', '/media/c.wav', '/media/d.wav', '/media/e.wav']);

    await userEvent.click(await screen.findByRole('button', { name: t('convert.submit') }));

    await waitFor(() => expect(created).toHaveLength(5));
    expect(created.every((body) => body.kind === 'media.convert' && body.params.target === 'mp3')).toBe(true);
    expect(created[0].params.options).toEqual({ vbr: 2 });
  });

  it('la tabla muestra el progreso de cada trabajo', async () => {
    jobs = [job({ id: 7, status: 'running', progress: 0.5, params: { input: '/media/a.wav', target: 'mp3' } })];
    renderPage();

    expect(await screen.findByText(t('media.status.running', { percent: 50 }))).toBeTruthy();
  });

  it('un error abre el diálogo con el detalle técnico del trabajo', async () => {
    jobs = [
      job({
        id: 3,
        status: 'error',
        error_code: 'codec_unavailable',
        error_detail: "Unknown encoder 'libopus'",
        params: { input: '/media/a.wav', target: 'ogg-opus' },
      }),
    ];
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.action.open_error') }));

    const dialog = await screen.findByRole('dialog', { name: t('convert.error.title') });
    expect(within(dialog).getByText("Unknown encoder 'libopus'")).toBeTruthy();
  });

  it('un video se convierte con el formato de video ★ y pide sus datos al server', async () => {
    renderPage();
    await drop(['/media/clip.mp4']);

    const format = (await screen.findByRole('combobox', { name: t('convert.format.label') })) as HTMLInputElement;
    expect(format.value).toContain(t('convert.format.mp4-h264'));
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/media/info?path='));
  });

  it('elegir archivos con el botón suma los que devuelve el diálogo', async () => {
    vi.mocked(open).mockResolvedValueOnce(['/media/picked.wav']);
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.files.pick') }));

    expect(await screen.findByText('picked.wav')).toBeTruthy();
  });

  it('un archivo que no es de medios se rechaza y no entra en la lista', async () => {
    renderPage();
    await drop(['/media/notas.txt']);

    expect(screen.getByText(t('media.files.empty'))).toBeTruthy();
  });

  it('cancelar un trabajo en curso lo pide al server', async () => {
    jobs = [job({ id: 7, status: 'running', progress: 0.5 })];
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.action.cancel') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs/7/cancel'));
  });

  it('reintentar un error lo vuelve a encolar en el server', async () => {
    jobs = [job({ id: 3, status: 'error', error_code: 'codec_unavailable' })];
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.action.retry') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs/3/retry'));
  });

  it('un trabajo listo muestra su estado y abre su carpeta; uno cancelado muestra el suyo', async () => {
    jobs = [
      job({ id: 4, status: 'done', output_dir: 'out/convert/4' }),
      job({ id: 5, status: 'cancelled', params: { input: '/media/b.wav', target: 'mp3' } }),
    ];
    renderPage();

    expect(await screen.findByText(t('media.status.done'))).toBeTruthy();
    expect(screen.getByText(t('media.status.cancelled'))).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: t('media.action.folder') }));

    expect(openPath).toHaveBeenCalledWith('out/convert/4');
  });

  it('cerrar el diálogo del error lo quita de la pantalla', async () => {
    jobs = [job({ id: 3, status: 'error', error_code: 'codec_unavailable', error_detail: 'x' })];
    renderPage();
    await userEvent.click(await screen.findByRole('button', { name: t('media.action.open_error') }));

    await userEvent.click((await screen.findAllByRole('button', { name: t('media.dialog.close') }))[0]);

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });
});

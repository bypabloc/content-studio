import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { open } from '@tauri-apps/plugin-dialog';
import { openPath } from '@tauri-apps/plugin-opener';

import { NormalizePage } from '@/features/normalize/NormalizePage';
import { t } from '@/shared/i18n/t';

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

const report = {
  before: { I: -30, TP: -3, LRA: 8 },
  after: { I: -16, TP: -1.2, LRA: 6 },
  mode: 'linear',
  target: -16,
};

let jobs: unknown[] = [];
let created: { kind: string; params: Record<string, unknown> }[] = [];

function job(overrides: Record<string, unknown>) {
  return {
    id: 1,
    kind: 'media.normalize',
    status: 'queued',
    progress: 0,
    stage: null,
    output_dir: 'out/normalize/1',
    params: { input: '/media/a.wav', preset: 'podcast', enhance: false },
    error_code: null,
    error_detail: null,
    ...overrides,
  };
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <NormalizePage />
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
    if (path === '/jobs?kind=media.normalize') return jobs;
    if (path === '/files?path=out%2Fnormalize%2F1%2Fresult.json') return report;
    if (path.startsWith('/settings/')) return { key: path, value: null };
    throw new Error(`GET inesperado: ${path}`);
  });
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({ key: path.replace('/settings/', ''), value: body.value }));
  api.post.mockImplementation(async (path: string, body: { kind: string; params: Record<string, unknown> }) => {
    if (path === '/jobs') {
      created.push(body);
      return job({ id: created.length, params: body.params });
    }
    if (path.endsWith('/retry')) return {};
    throw new Error(`POST inesperado: ${path}`);
  });
});

afterEach(() => {
  delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
  cleanup();
  api.get.mockReset();
  api.put.mockReset();
  api.post.mockReset();
  window.location.hash = '';
});

describe('NormalizePage', () => {
  it('carga en la lista el archivo recibido por el parámetro path', async () => {
    window.location.hash = '#/normalize?path=%2Fmedia%2Fvoz.wav';
    renderPage();

    expect(await screen.findByText('voz.wav')).toBeTruthy();
  });

  it('con audio, el preset ★ es podcast y se encola un trabajo por archivo', async () => {
    renderPage();
    await drop(['/media/a.wav', '/media/b.wav']);

    await userEvent.click(await screen.findByRole('button', { name: t('normalize.submit') }));

    await waitFor(() => expect(created).toHaveLength(2));
    expect(created[0]).toMatchObject({ kind: 'media.normalize', params: { preset: 'podcast', enhance: false } });
  });

  it('la tabla muestra la sonoridad antes y después de cada archivo normalizado', async () => {
    jobs = [job({ id: 1, status: 'done' })];
    renderPage();

    const row = await screen.findByRole('row', { name: /a\.wav/ });
    expect(await within(row).findByText('-30.0')).toBeTruthy();
    expect(within(row).getByText('-16.0')).toBeTruthy();
  });

  it('el A/B alterna entre el original y el normalizado', async () => {
    jobs = [job({ id: 1, status: 'done' })];
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.action.listen') }));
    const audio = document.querySelector('audio');
    expect(audio?.getAttribute('src')).toBe('file:///media/a.wav');

    await userEvent.click(screen.getByRole('button', { name: t('normalize.ab.normalized') }));
    expect(document.querySelector('audio')?.getAttribute('src')).toBe('file://out/normalize/1/normalized.wav');
  });

  it('una referencia de voz abre el diálogo con el motivo, no un error genérico', async () => {
    jobs = [
      job({
        id: 2,
        status: 'error',
        error_code: 'reference_protected',
        error_detail: 'reference/jhosse/a.wav',
        params: { input: '/media/reference/jhosse/a.wav', preset: 'podcast', enhance: false },
      }),
    ];
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.action.open_error') }));

    const dialog = await screen.findByRole('dialog', { name: t('normalize.error.title') });
    expect(within(dialog).getByText(t('error.reference_protected'))).toBeTruthy();
  });

  it('con video, el preset ★ es youtube', async () => {
    renderPage();
    await drop(['/media/clip.mp4']);

    const preset = (await screen.findByRole('combobox', { name: t('normalize.preset.label') })) as HTMLInputElement;
    expect(preset.value).toContain(t('normalize.preset.youtube'));
  });

  it('el preset personalizado pide el objetivo en LUFS y lo manda al trabajo', async () => {
    renderPage();
    await drop(['/media/a.wav']);

    await userEvent.click(await screen.findByRole('combobox', { name: t('normalize.preset.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('normalize.preset.custom') }));
    fireEvent.change(await screen.findByRole('spinbutton', { name: t('normalize.custom.target') }), { target: { value: '-14' } });
    await userEvent.click(screen.getByRole('button', { name: t('normalize.submit') }));

    await waitFor(() => expect(created[0]?.params).toMatchObject({ preset: 'custom', target: -14 }));
  });

  it('un archivo en curso muestra su porcentaje', async () => {
    jobs = [job({ id: 1, status: 'running', progress: 0.4 })];
    renderPage();

    expect(await screen.findByText(t('media.status.running', { percent: 40 }))).toBeTruthy();
  });

  it('un trabajo listo abre su carpeta de salida', async () => {
    jobs = [job({ id: 1, status: 'done' })];
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.action.folder') }));

    expect(openPath).toHaveBeenCalledWith('out/normalize/1');
  });

  it('reintentar un error lo vuelve a encolar en el server', async () => {
    jobs = [job({ id: 2, status: 'error', error_code: null, error_detail: null })];
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.action.retry') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs/2/retry'));
  });

  it('cerrar el diálogo del error lo quita de la pantalla', async () => {
    jobs = [job({ id: 2, status: 'error', error_code: 'reference_protected', error_detail: 'x' })];
    renderPage();
    await userEvent.click(await screen.findByRole('button', { name: t('media.action.open_error') }));

    await userEvent.click((await screen.findAllByRole('button', { name: t('media.dialog.close') }))[0]);

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });

  it('elegir archivos con el botón suma los que devuelve el diálogo', async () => {
    vi.mocked(open).mockResolvedValueOnce(['/media/picked.wav']);
    renderPage();

    await userEvent.click(await screen.findByRole('button', { name: t('media.files.pick') }));

    expect(await screen.findByText('picked.wav')).toBeTruthy();
  });

  it('un archivo que no es de medios no entra en la lista', async () => {
    renderPage();
    await drop(['/media/notas.txt']);

    expect(screen.getByText(t('media.files.empty'))).toBeTruthy();
  });

  it('si el server rechaza el lote, muestra su mensaje', async () => {
    api.post.mockRejectedValueOnce(new Error('Servidor ocupado'));
    renderPage();
    await drop(['/media/a.wav']);

    await userEvent.click(await screen.findByRole('button', { name: t('normalize.submit') }));

    expect(await screen.findByText('Servidor ocupado')).toBeTruthy();
  });
});

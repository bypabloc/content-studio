import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ExportDialog } from '@/features/editor/ExportDialog';
import { t } from '@/shared/i18n/t';

const { api, openPath } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), queryUrl: vi.fn((route: string, query: Record<string, string>) => `${route}?path=${query.path}`) },
  openPath: vi.fn(),
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openPath }));

const PATH = 'D:/out/editor/demo/project.json';
const MARKERS = [
  { id: 'm1', t: 3, label: 'Parte A', color: '#fff' },
  { id: 'm2', t: 7, label: 'Parte B', color: '#f00' },
];

beforeEach(() => {
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined);
  api.post.mockResolvedValue({ id: 7 });
  api.get.mockImplementation((url: string) => {
    if (url === '/jobs/7') return Promise.resolve({ id: 7, status: 'done', progress: 1, error_code: null });
    if (url.startsWith('/fs/list?')) return Promise.resolve({ entries: [{ kind: 'audio', path: 'D:/out/editor/demo/exports/demo.wav', modified: 5 }] });
    return Promise.reject(new Error('unknown endpoint'));
  });
  openPath.mockResolvedValue(undefined);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('ExportDialog', () => {
  it('encola el render, muestra su progreso y permite abrir la carpeta y reproducir', async () => {
    render(<ExportDialog path={PATH} duration={10} markers={[]} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));
    fireEvent.click(screen.getByRole('checkbox', { name: t('editor.export.audio_only') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.start') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs', {
      kind: 'editor.render',
      params: { doc: PATH, format: 'wav', name: 'demo', normalize: null },
    }));
    fireEvent.click(await screen.findByRole('button', { name: t('media.action.folder') }));
    expect(openPath).toHaveBeenCalledWith('D:/out/editor/demo/exports');
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.play') }));
    await waitFor(() => expect(api.queryUrl).toHaveBeenCalledWith('/fs/media', { path: 'D:/out/editor/demo/exports/demo.wav' }));
  });

  it('exporta MP4 recomendado por defecto con la calidad elegida', async () => {
    render(<ExportDialog path={PATH} duration={10} markers={[]} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));

    expect(screen.getByRole('spinbutton', { name: t('editor.export.quality') })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.start') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs', {
      kind: 'editor.render',
      params: { doc: PATH, format: 'mp4-h264', name: 'demo', normalize: null, quality: 19 },
    }));
  });

  it('deshabilita quemar sin libass y deja exportar SRT aparte', async () => {
    const user = userEvent.setup();
    api.get.mockImplementation((url: string) => {
      if (url === '/system') return Promise.resolve({ subtitles_filter: false });
      if (url === '/jobs/7') return Promise.resolve({ id: 7, status: 'done', progress: 1, error_code: null });
      return Promise.reject(new Error('unknown endpoint'));
    });
    render(<ExportDialog path={PATH} duration={10} markers={[]} hasSubtitles />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));
    const select = await screen.findByRole('combobox', { name: t('editor.export.subtitles') });
    await user.click(select);
    const burn = await screen.findByRole('option', { name: t('editor.export.subtitles.burn') });
    expect(burn.getAttribute('aria-disabled') === 'true' || burn.hasAttribute('disabled')).toBe(true);
    await user.click(await screen.findByRole('option', { name: t('editor.export.subtitles.srt') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.start') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs', {
      kind: 'editor.render',
      params: { doc: PATH, format: 'mp4-h264', name: 'demo', normalize: null, subtitle_mode: 'srt', quality: 19 },
    }));
    expect(screen.getByText(t('editor.export.no_libass'))).toBeTruthy();
  });

  it('reproduce el video exportado más reciente', async () => {
    api.get.mockImplementation((url: string) => {
      if (url === '/jobs/7') return Promise.resolve({ id: 7, status: 'done', progress: 1, error_code: null });
      if (url.startsWith('/fs/list?')) {
        return Promise.resolve({ entries: [{ kind: 'video', path: 'D:/out/editor/demo/exports/demo.mp4', modified: 5 }] });
      }
      return Promise.reject(new Error('unknown endpoint'));
    });
    const { container } = render(<ExportDialog path={PATH} duration={10} markers={[]} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.start') }));
    expect(api.post).toHaveBeenCalled();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/jobs/7'));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.play') }));

    await waitFor(() => expect(container.querySelector('video')).toBeTruthy());
    expect(api.queryUrl).toHaveBeenCalledWith('/fs/media', { path: 'D:/out/editor/demo/exports/demo.mp4' });
  });

  it('encola un trabajo por cada tramo delimitado por marcadores', async () => {
    render(<ExportDialog path={PATH} duration={10} markers={MARKERS} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.markers') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(3));
    expect(api.post).toHaveBeenNthCalledWith(1, '/jobs', expect.objectContaining({ params: expect.objectContaining({ start: 0, end: 3 }) }));
    expect(api.post).toHaveBeenNthCalledWith(2, '/jobs', expect.objectContaining({ params: expect.objectContaining({ start: 3, end: 7 }) }));
    expect(api.post).toHaveBeenNthCalledWith(3, '/jobs', expect.objectContaining({ params: expect.objectContaining({ start: 7, end: 10 }) }));
  });

  it('muestra las rutas de fuentes ausentes cuando falla la exportación', async () => {
    api.get.mockImplementation((url: string) => {
      if (url === '/jobs/7') {
        return Promise.resolve({
          id: 7,
          status: 'error',
          progress: 0,
          error_code: 'missing_source',
          error_detail: JSON.stringify({ error: 'missing_source', params: { paths: ['media/tono.wav'] } }),
        });
      }
      return Promise.reject(new Error('unknown endpoint'));
    });
    render(<ExportDialog path={PATH} duration={10} markers={[]} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.start') }));

    expect((await screen.findByText(/media\/tono\.wav/)).textContent).toContain('media/tono.wav');
  });

  it('muestra un error genérico si el detalle del fallo no es válido', async () => {
    api.get.mockImplementation((url: string) =>
      url === '/jobs/7'
        ? Promise.resolve({ id: 7, status: 'error', progress: 0, error_code: 'missing_source', error_detail: 'invalid json' })
        : Promise.reject(new Error('unknown endpoint')),
    );
    render(<ExportDialog path={PATH} duration={10} markers={[]} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.start') }));

    expect(await screen.findByText(t('editor.export.failed'))).toBeTruthy();
  });

  it('manda la última salida de audio a Normalizar con su ruta', async () => {
    render(<ExportDialog path={PATH} duration={10} markers={[]} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.open') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.export.start') }));

    const actions = await screen.findByRole('group', { name: t('editor.send_to') });
    fireEvent.click(screen.getByRole('button', { name: t('normalize.submit') }));

    expect(window.location.hash).toBe(
      '#/normalize?path=D%3A%2Fout%2Feditor%2Fdemo%2Fexports%2Fdemo.wav',
    );
    expect(actions).toBeTruthy();
  });
});

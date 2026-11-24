import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MixPage } from '@/features/mix/MixPage';
import { t } from '@/shared/i18n/t';

const { api, open } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  open: vi.fn(),
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MixPage />
    </QueryClientProvider>,
  );
}

const PARAMS = {
  mode: 'transcript',
  duck_db: -12,
  ramp_ms: 300,
  music_db: -6,
  voice_db: 0,
  intro: 0,
  outro: 0,
  lufs: -14,
  merge_gap: 0.6,
  pre: 0.2,
  post: 0.4,
};

// Respuestas con la forma del server: /jobs es un arreglo, /mix/<id> el proyecto y /curve la envolvente.
async function serverGet(path: string) {
  if (path.startsWith('/jobs')) return [];
  if (path.endsWith('/curve')) return { total: 10, points: [] };
  if (path.startsWith('/mix/')) {
    const files = { voice: 'v.wav', music: 'm.wav', video: null, video_mode: 'replace' };
    return { id: 7, name: 'x', ...files, regions: [], params: PARAMS, transcribe_job: null, status: 'ready' };
  }
  return [];
}

beforeEach(() => {
  api.get.mockImplementation(serverGet);
  api.post.mockResolvedValue({ id: 7, status: 'ready', regions: [] });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('MixPage', () => {
  it('carga el medio enviado por path en la ranura compatible', async () => {
    window.location.hash = '#/mix?path=D%3A%2Fmedia%2Fclip.mp4';
    renderPage();

    expect(await screen.findByText('D:/media/clip.mp4')).toBeTruthy();
    expect(screen.getByRole('group', { name: t('mix.slot.video') }).textContent).toContain('D:/media/clip.mp4');
  });

  it('muestra tres ranuras (voz, música y video), cada una con su origen de archivo', async () => {
    renderPage();

    for (const slot of ['mix.slot.voice', 'mix.slot.music', 'mix.slot.video'] as const) {
      expect(await screen.findByRole('group', { name: t(slot) })).toBeTruthy();
    }
    expect(screen.getAllByRole('button', { name: t('mix.source.file') })).toHaveLength(3);
  });

  it('no crea el proyecto hasta tener la voz y la música', async () => {
    renderPage();

    const create = await screen.findByRole('button', { name: t('mix.create') });

    expect(create).toHaveProperty('disabled', true);
  });

  it('crea el proyecto con las rutas elegidas (el video es opcional)', async () => {
    open.mockResolvedValueOnce('D:/media/voz.wav').mockResolvedValueOnce('D:/media/musica.wav');
    renderPage();
    const files = await screen.findAllByRole('button', { name: t('mix.source.file') });
    await userEvent.click(files[0]);
    await userEvent.click(files[1]);

    fireEvent.click(screen.getByRole('button', { name: t('mix.create') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/mix/prepare', {
        voice: 'D:/media/voz.wav',
        music: 'D:/media/musica.wav',
        video: null,
        video_mode: 'replace',
      }),
    );
    // Regresión 019: el editor recién creado debe leer el proyecto del server, no un arreglo de /jobs sin params.
    expect(await screen.findByRole('combobox', { name: t('mix.mode.label') })).toBeTruthy();
  });

  it('el modo de video viaja con el proyecto', async () => {
    open
      .mockResolvedValueOnce('D:/media/voz.wav')
      .mockResolvedValueOnce('D:/media/musica.wav')
      .mockResolvedValueOnce('D:/media/video.mp4');
    renderPage();
    const files = await screen.findAllByRole('button', { name: t('mix.source.file') });
    await userEvent.click(files[0]);
    await userEvent.click(files[1]);
    await userEvent.click(files[2]);
    await userEvent.click(await screen.findByRole('combobox', { name: t('mix.video.mode.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('mix.video.under') }));

    fireEvent.click(screen.getByRole('button', { name: t('mix.create') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/mix/prepare',
        expect.objectContaining({ video: 'D:/media/video.mp4', video_mode: 'under' }),
      ),
    );
  });

  it('«Generar música para esta voz» abre Música con la voz como ?match=', async () => {
    open.mockResolvedValueOnce('D:/media/voz.wav');
    renderPage();
    await userEvent.click((await screen.findAllByRole('button', { name: t('mix.source.file') }))[0]);

    await userEvent.click(await screen.findByRole('button', { name: t('mix.music.generate') }));

    expect(decodeURIComponent(window.location.hash)).toBe('#/music?match=D:/media/voz.wav');
    window.location.hash = '';
  });

  it('«Volver» regresa a las ranuras después de crear el proyecto', async () => {
    open.mockResolvedValueOnce('D:/media/voz.wav').mockResolvedValueOnce('D:/media/musica.wav');
    renderPage();
    const files = await screen.findAllByRole('button', { name: t('mix.source.file') });
    await userEvent.click(files[0]);
    await userEvent.click(files[1]);
    fireEvent.click(screen.getByRole('button', { name: t('mix.create') }));

    await userEvent.click(await screen.findByRole('button', { name: t('mix.back') }));

    expect(await screen.findByRole('button', { name: t('mix.create') })).toBeTruthy();
  });

  it('si el server rechaza el proyecto, se queda en el formulario', async () => {
    open.mockResolvedValueOnce('D:/media/voz.wav').mockResolvedValueOnce('D:/media/musica.wav');
    api.post.mockRejectedValueOnce(new Error('ruta no permitida'));
    renderPage();
    const files = await screen.findAllByRole('button', { name: t('mix.source.file') });
    await userEvent.click(files[0]);
    await userEvent.click(files[1]);

    fireEvent.click(screen.getByRole('button', { name: t('mix.create') }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    expect(screen.getByRole('button', { name: t('mix.create') })).toBeTruthy();
  });

  it('spec 020: «Editar y repetir» de un render abre su proyecto de mezcla', async () => {
    window.location.hash = '#/mix?from_job=9';
    api.get.mockImplementation(async (path: string) =>
      path === '/jobs/9' ? { id: 9, kind: 'mix.render', params: { mix_id: 7 } } : serverGet(path),
    );
    renderPage();

    expect(await screen.findByRole('button', { name: t('mix.back') })).toBeTruthy();
  });

});

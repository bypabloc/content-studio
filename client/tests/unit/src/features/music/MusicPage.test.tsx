import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { open } from '@tauri-apps/plugin-dialog';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MusicPage } from '@/features/music/MusicPage';
import type { components } from '@/shared/api/schema';
import { label, t } from '@/shared/i18n/t';

type StyleOut = components['schemas']['StyleOut'];

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/shared/media/Player', () => ({ Player: () => null }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open: vi.fn() }));

const styles: StyleOut[] = [
  { key: 'lofi-chill', category: 'lofi', musical_key: 'C Major', bpm: 80, time_signature: '4', caption: 'lo-fi hip hop', has_sample: true, sample: 'out/samples/lofi-chill.wav' },
  { key: 'corporate-clean', category: 'corporate', musical_key: 'G Major', bpm: 110, time_signature: '4', caption: 'corporate piano', has_sample: false, sample: null },
];

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/music/styles') return { styles };
    if (path.startsWith('/settings/')) return { key: path.replace('/settings/', ''), value: null };
    return [];
  });
  api.post.mockImplementation(async () => ({ id: 1, group_key: null }));
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({ key: path.replace('/settings/', ''), value: body.value }));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MusicPage />
    </QueryClientProvider>,
  );
}

describe('MusicPage (spec 011, D-6, AC-8)', () => {
  it('WHEN se eligen 2 estilos y 2 variantes y se genera THEN se encola un solo trabajo music con esos parámetros', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole('button', { name: label('music.style', 'lofi-chill') }));
    await user.click(screen.getByRole('button', { name: label('music.style', 'corporate-clean') }));
    await user.click(screen.getByRole('button', { name: t('music.advanced') }));
    const variants = screen.getByRole('spinbutton', { name: t('music.options.variants') });
    await user.clear(variants);
    await user.type(variants, '2');
    await user.click(screen.getByRole('button', { name: t('music.generate') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', {
        kind: 'music',
        params: expect.objectContaining({
          model: 'acestep',
          style: ['lofi-chill', 'corporate-clean'],
          variants: 2,
          evaluate: true,
          retries: 1,
          no_lm: false,
          duration: 60,
        }),
      }),
    );
    expect(api.post.mock.calls.filter(([path]) => path === '/jobs')).toHaveLength(1);
  });

  it('WHEN se pulsa Ctrl+Enter con estilos elegidos THEN se genera, y sin estilos no', async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole('button', { name: label('music.style', 'lofi-chill') }));
    fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs', expect.objectContaining({ kind: 'music' })));

    api.post.mockClear();
    await user.click(screen.getByRole('button', { name: label('music.style', 'lofi-chill') }));
    fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });

    expect(api.post).not.toHaveBeenCalled();
  });

  it('WHEN se marca un estilo con ★ THEN la lista de favoritos se guarda en ajustes', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click((await screen.findAllByRole('button', { name: t('music.style.favorite') }))[1]);

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/music.favorites', { value: ['corporate-clean'] }));
  });

  it('WHEN se pulsa ▶ de un estilo con muestra THEN se pide su muestra', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole('button', { name: t('music.style.play', { style: label('music.style', 'lofi-chill') }) }));

    await waitFor(() => expect(api.get).toHaveBeenCalledWith(expect.stringContaining(encodeURIComponent('out/samples/lofi-chill.wav'))));
  });

  it('WHEN en Texto libre falta el BPM THEN Generar queda deshabilitado; completo, se encola con tonalidad, BPM y compás', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole('button', { name: t('music.mode.free') }));
    await user.type(screen.getByRole('textbox', { name: t('music.freeText.caption') }), 'warm lofi piano');
    await user.click(screen.getByRole('button', { name: 'C Major' }));
    expect((screen.getByRole('button', { name: t('music.generate') }) as HTMLButtonElement).disabled).toBe(true);

    await user.click(screen.getByRole('button', { name: t('music.freeText.tap') }));
    const bpm = screen.getByRole('spinbutton', { name: t('music.freeText.bpm') });
    await user.clear(bpm);
    await user.type(bpm, '90');
    expect((screen.getByRole('button', { name: t('music.generate') }) as HTMLButtonElement).disabled).toBe(false);
    await user.click(screen.getByRole('button', { name: t('music.generate') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', {
        kind: 'music',
        params: expect.objectContaining({
          style: ['warm lofi piano'],
          key: 'C Major',
          bpm: 90,
          time_signature: '4',
        }),
      }),
    );
  });

  it('WHEN se generó THEN la comparación del pedido aparece debajo del botón', async () => {
    const user = userEvent.setup();
    api.post.mockResolvedValueOnce({ id: 5, group_key: 'music:abc', status: 'queued' });
    renderPage();
    await user.click(await screen.findByRole('button', { name: label('music.style', 'lofi-chill') }));

    await user.click(screen.getByRole('button', { name: t('music.generate') }));

    expect(await screen.findByText(t('music.compare.empty'))).not.toBeNull();
  });

  it('WHEN se iguala a una narración terminada THEN la duración es la suya más la cola', async () => {
    const user = userEvent.setup();
    api.get.mockImplementation(async (path: string) => {
      if (path === '/music/styles') return { styles };
      if (path.startsWith('/jobs?kind=narration')) {
        return [{ id: 3, status: 'done', kind: 'narration', params: { text: 'Hola' }, output_dir: 'out/narration/n', starred: false }];
      }
      if (path.includes('script.json')) return { wav: 'n.wav' };
      if (path.startsWith('/media/info')) return { duration: 47.3 };
      if (path.startsWith('/settings/')) return { key: path.replace('/settings/', ''), value: null };
      return [];
    });
    renderPage();

    await user.click(await screen.findByRole('button', { name: t('music.duration.match') }));
    await user.click(await screen.findByRole('button', { name: /Hola/ }));

    expect((screen.getByRole('textbox', { name: t('music.duration.label') }) as HTMLInputElement).value).toBe('00:49.3');
  });

  it('WHEN se iguala a un archivo THEN usa su duración más la cola', async () => {
    const user = userEvent.setup();
    vi.mocked(open).mockResolvedValueOnce('/media/video.mp4');
    api.get.mockImplementation(async (path: string) => {
      if (path === '/music/styles') return { styles };
      if (path.startsWith('/media/info')) return { duration: 125 };
      if (path.startsWith('/settings/')) return { key: path.replace('/settings/', ''), value: null };
      return [];
    });
    renderPage();

    await user.click(await screen.findByRole('button', { name: t('music.duration.match') }));
    await user.click(screen.getByRole('button', { name: t('music.duration.matchFile') }));

    await waitFor(() => expect((screen.getByRole('textbox', { name: t('music.duration.label') }) as HTMLInputElement).value).toBe('02:07.0'));
  });
});

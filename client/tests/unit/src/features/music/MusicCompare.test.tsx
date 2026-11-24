import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { MusicCompare } from '@/features/music/MusicCompare';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => path },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@/shared/media/Player', () => ({ Player: () => null }));

const job = { id: 7, kind: 'music', status: 'done', group_key: 'music:abc', output_dir: 'out/music/x' };
const manifest = {
  chosen: 'acestep-corporate-v2.wav',
  tracks: [
    { file: 'acestep-lofi-chill-v1.wav', style: 'lofi-chill', variant: 1, requested: 30, duration: 30.02, warning: null, voice: false, lufs: -16.1, key: 'C Major', bpm: 80 },
    { file: 'acestep-lofi-chill-v2.wav', style: 'lofi-chill', variant: 2, requested: 30, duration: 30.0, warning: null, voice: true, lufs: -15.8, key: 'C Major', bpm: 80 },
    { file: 'acestep-corporate-v1.wav', style: 'corporate', variant: 1, requested: 30, duration: 24.1, warning: 'music_short', voice: null, lufs: -17.0, key: 'G Major', bpm: 110 },
    { file: 'acestep-corporate-v2.wav', style: 'corporate', variant: 2, requested: 30, duration: 30.0, warning: null, voice: false, lufs: -16.4, key: 'G Major', bpm: 110 },
  ],
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.location.hash = '';
});

function renderCompare() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MusicCompare groupKey="music:abc" />
    </QueryClientProvider>,
  );
}

describe('MusicCompare (spec 011, D-6, AC-8)', () => {
  it('abre en el Editor con la ruta de una pista', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path.startsWith('/jobs?group_key=')) return [job];
      if (path.includes('tracks.json')) return manifest;
      return { peaks: [] };
    });

    renderCompare();
    await waitFor(() => expect(document.querySelectorAll('[data-track]')).toHaveLength(4));
    await userEvent.click(screen.getAllByRole('button', { name: 'Abrir en Editor' })[0]);

    expect(new URLSearchParams(window.location.hash.split('?')[1]).getAll('add')).toEqual([
      'out/music/x/acestep-lofi-chill-v1.wav',
    ]);
  });

  it('WHEN se eligen 2 estilos y 2 variantes THEN compara las 4 pistas con su duración real y su voz', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path.startsWith('/jobs?group_key=')) return [job];
      if (path.includes('tracks.json')) return manifest;
      return { peaks: [] };
    });

    renderCompare();

    await waitFor(() => expect(document.querySelectorAll('[data-track]')).toHaveLength(4));
    expect(screen.queryAllByText(t('music.compare.seconds', { n: '30.0' }))).toHaveLength(3);
    expect(screen.queryByText(t('warning.music_short', { n: '24.1' }))).not.toBeNull();
    expect(screen.queryByText(t('music.compare.voice.yes'))).not.toBeNull();
  });

  it('WHEN se elige una pista THEN se manda al trabajo de esa pista y queda como la única elegida', async () => {
    const user = userEvent.setup();
    api.get.mockImplementation(async (path: string) => {
      if (path.startsWith('/jobs?group_key=')) return [job];
      if (path.includes('tracks.json')) return manifest;
      return { peaks: [] };
    });
    api.post.mockResolvedValue({});

    renderCompare();
    await waitFor(() => expect(document.querySelectorAll('[data-track]')).toHaveLength(4));
    await user.click(screen.getAllByRole('button', { name: t('music.compare.choose') })[1]);

    expect(api.post).toHaveBeenCalledWith('/jobs/7/choose', { file: 'acestep-lofi-chill-v2.wav' });
  });

  it('WHEN se pulsa «Mandar a Mezclar» THEN Mezcla abre con la pista elegida (spec 016, D-4)', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path.startsWith('/jobs?group_key=')) return [job];
      if (path.includes('tracks.json')) return manifest;
      return { peaks: [] };
    });

    renderCompare();
    await waitFor(() => expect(document.querySelectorAll('[data-track]')).toHaveLength(4));
    await userEvent.click(screen.getByRole('button', { name: t('mix.send') }));

    expect(window.location.hash).toBe('#/mix?path=out%2Fmusic%2Fx%2Facestep-corporate-v2.wav');
    window.location.hash = '';
  });

  it('sin pista elegida, «Mandar a Mezclar» está deshabilitado', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path.startsWith('/jobs?group_key=')) return [job];
      if (path.includes('tracks.json')) return { ...manifest, chosen: null };
      return { peaks: [] };
    });

    renderCompare();
    await waitFor(() => expect(document.querySelectorAll('[data-track]')).toHaveLength(4));

    expect(screen.getByRole('button', { name: t('mix.send') })).toHaveProperty('disabled', true);
  });
});

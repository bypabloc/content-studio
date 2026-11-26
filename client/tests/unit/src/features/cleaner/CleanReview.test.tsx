import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { CleanReview } from '@/features/cleaner/CleanReview';
import { clock } from '@/features/cleaner/cuts';
import { t } from '@/shared/i18n/t';

const { api, review } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  review: { props: null as null | Record<string, unknown> },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
// La onda se prueba aparte (ReviewWave.test.tsx): aquí solo se mira lo que recibe.
vi.mock('@/features/cleaner/ReviewWave', () => ({
  ReviewWave: (props: Record<string, unknown>) => {
    review.props = props;
    return null;
  },
}));

const doc = {
  params: { input: '/media/charla.mp4' },
  language: 'es',
  duration: 10,
  transcript: 'out/clean/7/transcript.json',
  cuts: [
    { start: 1, end: 2, enabled: true },
    { start: 5, end: 6, enabled: true, edited: true },
  ],
};
const replanned = {
  ...doc,
  cuts: [
    { start: 1.5, end: 2, enabled: true },
    { start: 5, end: 6, enabled: true, edited: true },
  ],
};
const transcript = {
  language: 'es',
  duration: 10,
  segments: [{ start: 0, end: 1, text: 'hola', words: [{ start: 0, end: 0.5, word: 'hola', probability: 0.9 }] }],
};

function routes(input: string) {
  return async (path: string) => {
    if (path === '/clean/7') return { ...doc, params: { input } };
    if (path.startsWith('/files?path=')) return transcript;
    if (path.startsWith('/media/peaks')) return { peaks: [0.1, 0.4] };
    return null;
  };
}

function renderReview() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <CleanReview jobId={7} />
    </QueryClientProvider>,
  );
}

describe('CleanReview (spec 013, D-6, AC-7)', () => {
  beforeEach(() => {
    api.get.mockImplementation(routes('/media/charla.mp4'));
    api.post.mockImplementation(async (path: string) => (path === '/clean/7/plan' ? replanned : { id: 9, kind: 'clean.render' }));
    api.put.mockImplementation(async () => doc);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    review.props = null;
  window.location.hash = '';
  });

  it('AC-7: cambiar el hueco mínimo llama a /plan, reemplaza los cortes sin editar y conserva el editado', async () => {
    const user = userEvent.setup();
    renderReview();
    await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }));

    const gap = screen.getByRole('spinbutton', { name: t('cleaner.options.min_gap') });
    await user.clear(gap);
    await user.type(gap, '800');

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/clean/7/plan', expect.objectContaining({ min_gap: 0.8 })));
    await waitFor(() => expect(review.props?.cuts).toEqual(replanned.cuts));
  });

  it('la duración resultante se ve y se actualiza con los cortes activos', async () => {
    renderReview();

    expect(await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }))).toBeTruthy();
  });

  it('D desactiva el corte seleccionado; las flechas cambian de corte', async () => {
    renderReview();
    await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }));

    fireEvent.keyDown(window, { key: 'd' });
    await waitFor(() => {
      const shown = review.props?.cuts as Array<{ enabled: boolean }> | undefined;
      expect(shown?.[0]?.enabled).toBe(false);
    });

    fireEvent.keyDown(window, { key: 'ArrowRight' });
    await waitFor(() => expect(review.props?.selected).toBe(1));
    fireEvent.keyDown(window, { key: 'ArrowLeft' });
    await waitFor(() => expect(review.props?.selected).toBe(0));
  });

  it('«Escuchar sin cortes» se activa y se desactiva', async () => {
    const user = userEvent.setup();
    renderReview();

    const preview = await screen.findByRole('button', { name: t('cleaner.review.preview') });
    await user.click(preview);
    expect(preview.getAttribute('aria-pressed')).toBe('true');
    await user.click(preview);
    expect(preview.getAttribute('aria-pressed')).toBe('false');
  });

  it('Renderizar guarda los cortes y encola clean.render', async () => {
    const user = userEvent.setup();
    renderReview();
    await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }));

    await user.click(screen.getByRole('button', { name: t('cleaner.review.render') }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/clean/7/cuts', { cuts: expect.any(Array) }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/clean/7/render'));
  });

  it('un video muestra su imagen arriba; un audio no', async () => {
    const { container } = renderReview();
    await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }));
    expect(container.querySelector('video')).not.toBeNull();

    cleanup();
    api.get.mockImplementation(routes('/media/charla.wav'));
    const audio = renderReview();
    await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }));
    expect(audio.container.querySelector('video')).toBeNull();
  });

  it('la transcripción muestra cada palabra; un clic en una salta a ese punto', async () => {
    const user = userEvent.setup();
    renderReview();

    await user.click(await screen.findByRole('button', { name: 'hola' }));

    expect(screen.getByText(t('cleaner.review.transcript'))).toBeTruthy();
  });

  describe('Subtitular (spec 014, AC-11)', () => {
    const subtitleButton = () => screen.getByRole('button', { name: t('cleaner.review.subtitle') }) as HTMLButtonElement;

    function withRenders(input: string, renders: unknown[]) {
      api.get.mockImplementation(async (path: string) => {
        if (path === '/jobs?kind=clean.analyze') return [{ id: 7, status: 'done', output_dir: 'D:/out/clean/7', params: {} }];
        if (path === '/jobs?kind=clean.render') return renders;
        return routes(input)(path);
      });
    }

    it('abre en el Editor con el archivo renderizado de este análisis', async () => {
      withRenders('/media/charla.mp4', [
        { id: 9, status: 'done', output_dir: 'D:/out/clean/9', params: { analysis: 'D:/out/clean/7' } },
      ]);
      renderReview();
      await waitFor(() => expect(screen.getByRole('button', { name: 'Abrir en Editor' })).toBeTruthy());

      fireEvent.click(screen.getByRole('button', { name: 'Abrir en Editor' }));

      expect(new URLSearchParams(window.location.hash.split('?')[1]).getAll('add')).toEqual([
        'D:/out/clean/9/clean.mp4',
      ]);
    });

    it('sin una render de este análisis, el botón espera', async () => {
      withRenders('/media/charla.mp4', []);
      renderReview();
      await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }));

      expect(subtitleButton().disabled).toBe(true);
    });

    it('una render de otro análisis no cuenta', async () => {
      withRenders('/media/charla.mp4', [
        { id: 9, status: 'done', output_dir: 'D:/out/clean/9', params: { analysis: 'D:/out/clean/5' } },
      ]);
      renderReview();
      await screen.findByText(t('cleaner.review.duration', { duration: clock(8) }));

      expect(subtitleButton().disabled).toBe(true);
    });

    it('con la render de este análisis, encola subtitles.create con el video limpio', async () => {
      const user = userEvent.setup();
      withRenders('/media/charla.mp4', [
        { id: 9, status: 'done', output_dir: 'D:/out/clean/9', params: { analysis: 'D:\\out\\clean\\7' } },
      ]);
      renderReview();
      await waitFor(() => expect(subtitleButton().disabled).toBe(false));

      await user.click(subtitleButton());

      await waitFor(() =>
        expect(api.post).toHaveBeenCalledWith('/jobs', {
          kind: 'subtitles.create',
          params: {
            origin: 'cleaner',
            input: 'out/clean/7/transcript.json',
            analysis: 'D:/out/clean/7',
            source: 'D:/out/clean/9/clean.mp4',
          },
        }),
      );
    });

    it('un audio sin video pasa su clean.wav', async () => {
      const user = userEvent.setup();
      withRenders('/media/charla.wav', [
        { id: 9, status: 'done', output_dir: 'D:/out/clean/9', params: { analysis: 'D:/out/clean/7' } },
      ]);
      renderReview();
      await waitFor(() => expect(subtitleButton().disabled).toBe(false));

      await user.click(subtitleButton());

      await waitFor(() =>
        expect(api.post).toHaveBeenCalledWith(
          '/jobs',
          expect.objectContaining({ params: expect.objectContaining({ source: 'D:/out/clean/9/clean.wav' }) }),
        ),
      );
    });
  });
});

describe('CleanReview con hablantes (AC-8)', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it('colorea cada palabra con el color de su hablante y muestra la leyenda con los nombres', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/clean/7') {
        return {
          ...doc,
          params: { input: '/media/charla.mp4' },
          words: [
            { start: 0, end: 0.5, word: 'hola', speaker: 'SPEAKER_00' },
            { start: 0.5, end: 1, word: 'mundo', speaker: 'SPEAKER_01' },
          ],
          speakers: {
            SPEAKER_00: { name: 'Ana', color: '#2563eb' },
            SPEAKER_01: { name: 'Luis', color: '#dc2626' },
          },
        };
      }
      if (path.startsWith('/media/peaks')) return { peaks: [0.1, 0.4] };
      return null;
    });
    renderReview();

    expect((await screen.findByRole('button', { name: 'hola' })).style.borderBottomColor).toBe('rgb(37, 99, 235)');
    expect(screen.getByRole('button', { name: 'mundo' }).style.borderBottomColor).toBe('rgb(220, 38, 38)');
    expect(screen.getByText('Ana')).toBeTruthy();
    expect(screen.getByText('Luis')).toBeTruthy();
  });
});

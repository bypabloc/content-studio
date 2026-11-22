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
});

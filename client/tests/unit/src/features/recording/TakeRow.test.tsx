import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TakeRow } from '@/features/recording/TakeRow';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    fileUrl: (path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`,
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

// WaveSurfer no corre fuera del navegador: el stub deja ver qué audio recibe el reproductor.
vi.mock('@/shared/media/Player', async () => {
  const { createElement } = await import('react');
  return { Player: ({ src }: { src: string }) => createElement('p', null, `reproductor ${src}`) };
});

const PATH = 'server/data/narration/reference/spec-010/takes/expert/3.wav';
const OK = { verdict: 'ok', reasons: [], notes: [], messages: [], measures: {} };
const RETAKE = { verdict: 'retake', reasons: ['edges', 'noise'], notes: [], messages: [], measures: {} };

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderRow(check: unknown): void {
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/media/peaks')) return { peaks: [0.5] };
    return { take: 3, path: PATH, check };
  });
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <TakeRow slug="spec-010" style="expert" take={3} />
    </QueryClientProvider>,
  );
}

describe('TakeRow (spec 010, D-6)', () => {
  it('una toma sin chequeo dice que se está chequeando', async () => {
    renderRow(null);

    expect(await screen.findByText(t('voices.take.pending'))).toBeTruthy();
  });

  it('una toma buena dice que está bien', async () => {
    renderRow(OK);

    expect(await screen.findByText(t('voices.take.ok'))).toBeTruthy();
  });

  it('una toma para repetir dice por qué, con el texto de cada razón', async () => {
    renderRow(RETAKE);

    expect(await screen.findByText(t('voices.take.retake'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.edges'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.noise'))).toBeTruthy();
  });

  it('la toma se reproduce desde su ruta, con su forma de onda', async () => {
    renderRow(OK);

    expect(await screen.findByText(`reproductor ${api.fileUrl(PATH)}`)).toBeTruthy();
  });

  it('elegir la toma la manda a la referencia del estilo', async () => {
    api.post.mockResolvedValue({ style: 'expert', take: 3 });
    renderRow(OK);

    fireEvent.click(await screen.findByRole('button', { name: t('action.choose') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/voices/profiles/spec-010/takes/expert/3/choose'));
  });

  it('cada razón y cada nota del chequeo se dice con su texto; un código desconocido se muestra tal cual', async () => {
    renderRow({
      verdict: 'retake',
      reasons: ['too_long', 'too_short', 'peak_high', 'peak_low', 'pause', 'text', 'whisper_missing', 'codigo_nuevo'],
      notes: ['resampled'],
      messages: [],
      measures: {},
    });

    expect(await screen.findByText(t('voice.check.too_long'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.too_short'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.peak_high'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.peak_low'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.pause'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.text'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.whisper_missing'))).toBeTruthy();
    expect(screen.getByText(t('voice.check.resampled'))).toBeTruthy();
    expect(screen.getByText('codigo_nuevo')).toBeTruthy();
  });
});

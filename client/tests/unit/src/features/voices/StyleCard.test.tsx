import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { StyleCard } from '@/features/voices/StyleCard';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    fileUrl: (path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`,
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

// WaveSurfer no corre fuera del navegador: el stub deja ver el audio y la cantidad de picos que recibe.
vi.mock('@/shared/media/Player', async () => {
  const { createElement } = await import('react');
  return {
    Player: ({ src, peaks }: { src: string; peaks: number[] }) => createElement('p', null, `reproductor ${src} ${peaks.length}`),
  };
});

beforeEach(() => {
  api.get.mockResolvedValue({ peaks: [0.5] });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderCard(item: Parameters<typeof StyleCard>[0]['item']): void {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <StyleCard item={item} />
    </QueryClientProvider>,
  );
}

describe('StyleCard (spec 010, D-6)', () => {
  it('sin referencia dice que falta y no pide picos', () => {
    renderCard({ style: 'expert', chosen: false, takes: 0, reference: null });

    expect(screen.getByText(t('label.narration.style.expert'))).toBeTruthy();
    expect(screen.getByText(t('voices.style.missing'))).toBeTruthy();
    expect(screen.getByText(t('voices.takes', { count: 0 }))).toBeTruthy();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('con referencia elegida cuenta las tomas y reproduce la referencia con sus picos', async () => {
    renderCard({ style: 'neutral', chosen: true, takes: 3, reference: 'ref/neutral.wav' });

    expect(screen.getByText(t('voices.style.chosen'))).toBeTruthy();
    expect(screen.getByText(t('voices.takes', { count: 3 }))).toBeTruthy();
    expect(await screen.findByText(`reproductor ${api.fileUrl('ref/neutral.wav')} 1`)).toBeTruthy();
  });
});

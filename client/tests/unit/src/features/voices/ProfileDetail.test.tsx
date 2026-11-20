import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProfileDetail } from '@/features/voices/ProfileDetail';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    fileUrl: (path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`,
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

// WaveSurfer no corre fuera del navegador: el stub solo deja ver qué audio y qué picos recibe el reproductor.
vi.mock('@/shared/media/Player', async () => {
  const { createElement } = await import('react');
  return {
    Player: ({ src, peaks }: { src: string; peaks: number[] }) => createElement('p', null, `reproductor ${src} ${peaks.length}`),
  };
});

const REFERENCE = 'server/data/narration/reference/spec-010/neutral.wav';
const PROFILE = {
  id: 'spec-010',
  name: 'Spec 010',
  styles: [
    { style: 'neutral', chosen: true, takes: 2, reference: REFERENCE },
    { style: 'expert', chosen: false, takes: 0, reference: null },
  ],
};

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => (path.startsWith('/media/peaks') ? { peaks: [0.2, 0.4] } : PROFILE));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderDetail(onBack: () => void = () => {}): void {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <ProfileDetail slug="spec-010" onBack={onBack} />
    </QueryClientProvider>,
  );
}

describe('ProfileDetail (spec 010, D-6)', () => {
  it('muestra cada estilo con si tiene referencia elegida y cuántas tomas tiene', async () => {
    renderDetail();

    expect(await screen.findByText(t('label.narration.style.neutral'))).toBeTruthy();
    expect(screen.getByText(t('label.narration.style.expert'))).toBeTruthy();
    expect(screen.getByText(t('voices.takes', { count: 2 }))).toBeTruthy();
    expect(screen.getAllByText(t('voices.style.chosen'))).toHaveLength(1);
    expect(screen.getAllByText(t('voices.style.missing'))).toHaveLength(1);
  });

  it('la referencia elegida se reproduce con su forma de onda, pidiendo los picos al server', async () => {
    renderDetail();

    expect(await screen.findByText(`reproductor ${api.fileUrl(REFERENCE)} 2`)).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith(`/media/peaks?path=${encodeURIComponent(REFERENCE)}&n=2000`);
  });

  it('volver llama a onBack', async () => {
    const onBack = vi.fn();
    renderDetail(onBack);

    fireEvent.click(await screen.findByRole('button', { name: t('voices.back') }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});

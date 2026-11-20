import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TakeList } from '@/features/recording/TakeList';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    fileUrl: (path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`,
  },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

vi.mock('@/shared/media/Player', async () => {
  const { createElement } = await import('react');
  return { Player: ({ src }: { src: string }) => createElement('p', null, `reproductor ${src}`) };
});

const OK = { verdict: 'ok', reasons: [], notes: [], messages: [], measures: {} };

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderList(takes: number[]): void {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/voices/profiles/spec-010/takes/expert') return { style: 'expert', takes };
    if (path.startsWith('/media/peaks')) return { peaks: [0.5] };
    const take = /\/takes\/expert\/(\d+)$/.exec(path);
    return take ? { take: Number(take[1]), path: `p${take[1]}`, check: OK } : {};
  });
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <TakeList slug="spec-010" style="expert" />
    </QueryClientProvider>,
  );
}

describe('TakeList (spec 010, D-6)', () => {
  it('lista las tomas del estilo, la más nueva primero', async () => {
    renderList([1, 2]);

    const titles = await screen.findAllByRole('heading', { level: 3 });
    expect(titles.map((title) => title.textContent)).toEqual([t('voices.take.title', { n: 2 }), t('voices.take.title', { n: 1 })]);
  });

  it('sin tomas lo dice', async () => {
    renderList([]);

    expect(await screen.findByText(t('voices.takes.empty'))).toBeTruthy();
  });
});

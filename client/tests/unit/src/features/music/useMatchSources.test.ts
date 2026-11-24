import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useMatchSources } from '@/features/music/useMatchSources';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const jobs = [
  { id: 1, kind: 'narration', status: 'done', params: { text: 'Hola mundo' }, output_dir: 'out/narration/a', starred: false },
  { id: 2, kind: 'narration', status: 'done', params: { text: 'Adiós' }, output_dir: 'out/narration/b', starred: true },
  { id: 3, kind: 'narration', status: 'done', params: {}, output_dir: null, starred: false },
];

function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client: new QueryClient({ defaultOptions: { queries: { retry: false } } }) }, children);
}

afterEach(() => {
  vi.clearAllMocks();
});

describe('useMatchSources (spec 011, D-4, AC-6)', () => {
  it('WHEN hay narraciones terminadas con carpeta THEN da su duración real, con ★ primero', async () => {
    api.get.mockImplementation(async (path: string) => {
      const decoded = decodeURIComponent(path);
      if (path.startsWith('/jobs?kind=narration')) return jobs;
      if (decoded.endsWith('/script.json')) return { wav: decoded.includes('/b/') ? 'b.wav' : 'a.wav' };
      if (decoded.includes('/b/b.wav')) return { duration: 30 };
      return { duration: 47.3 };
    });

    const { result } = renderHook(() => useMatchSources(), { wrapper });

    await waitFor(() => expect(result.current).toHaveLength(2));
    expect(result.current).toEqual([
      { id: '2', label: 'Adiós', starred: true, duration: 30 },
      { id: '1', label: 'Hola mundo', starred: false, duration: 47.3 },
    ]);
  });

  it('WHEN no hay narraciones THEN la lista está vacía', async () => {
    api.get.mockResolvedValue([]);

    const { result } = renderHook(() => useMatchSources(), { wrapper });

    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(result.current).toEqual([]);
  });
});

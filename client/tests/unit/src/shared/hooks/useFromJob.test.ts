import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { textParam, useFromJob } from '@/shared/hooks/useFromJob';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: new QueryClient({ defaultOptions: { queries: { retry: false } } }) }, children);

afterEach(() => {
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('useFromJob (spec 020, D-4)', () => {
  it('con ?from_job= trae el trabajo y sus parámetros', async () => {
    window.location.hash = '#/music?from_job=7';
    api.get.mockResolvedValue({ id: 7, kind: 'music', params: { duration: 30, style: ['lofi'] } });

    const { result } = renderHook(() => useFromJob(), { wrapper });

    await waitFor(() => expect(result.current?.id).toBe(7));
    expect(api.get).toHaveBeenCalledWith('/jobs/7');
    expect(textParam(result.current!, 'style', 'x')).toBe('x');
  });

  it('sin from_job, o con uno que no es un número, no pide nada', () => {
    window.location.hash = '#/music?from_job=abc';
    const { result } = renderHook(() => useFromJob(), { wrapper });

    expect(result.current).toBeNull();
    expect(api.get).not.toHaveBeenCalled();
    expect(textParam({ id: 1, kind: 'narration', params: { text: 'hola' } }, 'text')).toBe('hola');
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';

import { recommendedValue, useRecommendedValue } from '@/shared/hooks/useRecommendedValue';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const options = [{ value: 'mp3' }, { value: 'wav', recommended: true }, { value: 'flac' }];

// Sin JSX: este archivo es .ts, como su módulo.
function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client: new QueryClient({ defaultOptions: { queries: { retry: false } } }) }, children);
}

describe('recommendedValue', () => {
  it('es la recomendada, o la primera si ninguna lo es', () => {
    expect(recommendedValue(options)).toBe('wav');
    expect(recommendedValue([{ value: 'a' }, { value: 'b' }])).toBe('a');
    expect(recommendedValue([])).toBe('');
  });
});

describe('useRecommendedValue', () => {
  it('sin elección guardada vale la recomendada', async () => {
    api.get.mockResolvedValue({ key: 'select.test', value: null });

    const { result } = renderHook(() => useRecommendedValue('select.test', options), { wrapper });

    expect(result.current[0]).toBe('wav');
  });

  it('una elección guardada que todavía existe se respeta', async () => {
    api.get.mockResolvedValue({ key: 'select.test', value: 'flac' });

    const { result } = renderHook(() => useRecommendedValue('select.test', options), { wrapper });

    await waitFor(() => expect(result.current[0]).toBe('flac'));
  });

  it('una elección guardada que ya no es una opción vale la recomendada', async () => {
    api.get.mockResolvedValue({ key: 'select.test', value: 'aiff' });

    const { result } = renderHook(() => useRecommendedValue('select.test', options), { wrapper });

    await waitFor(() => expect(result.current[0]).toBe('wav'));
  });
});

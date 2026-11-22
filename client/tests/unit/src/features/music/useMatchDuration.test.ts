import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useMatchDuration } from '@/features/music/useMatchDuration';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function wrapper({ children }: { children: ReactNode }) {
  return createElement(QueryClientProvider, { client }, children);
}

beforeEach(() => {
  api.get.mockResolvedValue({ duration: 12.5 });
  window.location.hash = '#/music?match=D%3A%2Fmedia%2Fvoz.wav&tail=3';
});

afterEach(() => {
  client.clear();
  window.location.hash = '';
  vi.clearAllMocks();
});

describe('useMatchDuration (spec 016, D-4: ?match= desde Mezcla)', () => {
  it('iguala la duración a la de la voz más la cola (intro + outro)', async () => {
    const { result } = renderHook(() => useMatchDuration(), { wrapper });

    await waitFor(() => expect(result.current).toBe(15.5));
    expect(api.get).toHaveBeenCalledWith('/media/info?path=D%3A%2Fmedia%2Fvoz.wav');
  });

  it('sin ?match= no iguala nada y no pide la duración', () => {
    window.location.hash = '#/music';

    const { result } = renderHook(() => useMatchDuration(), { wrapper });

    expect(result.current).toBeNull();
    expect(api.get).not.toHaveBeenCalled();
  });
});

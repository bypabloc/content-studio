import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useMediaInfo, useMediaPeaks } from '@/shared/media/useMediaInfo';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function withClient() {
  const client = new QueryClient();
  return ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client }, children);
}

describe('useMediaInfo', () => {
  it('pide la duración, el LUFS y el pico real del archivo', async () => {
    api.get.mockResolvedValue({ duration: 12.5, lufs: -16.2, true_peak: -1.4 });
    const { result } = renderHook(() => useMediaInfo('D:/out/a b.wav'), { wrapper: withClient() });

    await waitFor(() => expect(result.current.data).toEqual({ duration: 12.5, lufs: -16.2, true_peak: -1.4 }));
    expect(api.get).toHaveBeenCalledWith('/media/info?path=D%3A%2Fout%2Fa%20b.wav');
  });

  it('sin ruta no pide nada', () => {
    renderHook(() => useMediaInfo(''), { wrapper: withClient() });

    expect(api.get).not.toHaveBeenCalled();
  });
});

describe('useMediaPeaks', () => {
  it('pide los picos con el número de muestras que se le da', async () => {
    api.get.mockResolvedValue({ peaks: [0.2, 0.4] });
    const { result } = renderHook(() => useMediaPeaks('a.wav', 300), { wrapper: withClient() });

    await waitFor(() => expect(result.current.data).toEqual({ peaks: [0.2, 0.4] }));
    expect(api.get).toHaveBeenCalledWith('/media/peaks?path=a.wav&n=300');
  });

  it('sin número de muestras pide 2000', async () => {
    api.get.mockResolvedValue({ peaks: [] });
    renderHook(() => useMediaPeaks('a.wav'), { wrapper: withClient() });

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/media/peaks?path=a.wav&n=2000'));
  });
});

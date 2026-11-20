import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChooseTake, useStyleTakes, useTakeDetail, useUploadTake } from '@/features/recording/useTakes';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn(), upload: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

function wrapperWith(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client }, children);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useTakes (spec 010, D-3)', () => {
  it('useStyleTakes pide los números de las tomas del estilo', async () => {
    api.get.mockResolvedValue({ style: 'expert', takes: [1, 2] });

    const { result } = renderHook(() => useStyleTakes('spec-010', 'expert'), { wrapper: wrapperWith(new QueryClient()) });

    await waitFor(() => expect(result.current.data?.takes).toEqual([1, 2]));
    expect(api.get).toHaveBeenCalledWith('/voices/profiles/spec-010/takes/expert');
  });

  it('useTakeDetail vuelve a pedir la toma mientras no tiene chequeo', async () => {
    api.get
      .mockResolvedValueOnce({ take: 1, path: 'p', check: null })
      .mockResolvedValue({ take: 1, path: 'p', check: { verdict: 'ok' } });

    const { result } = renderHook(() => useTakeDetail('spec-010', 'expert', 1), { wrapper: wrapperWith(new QueryClient()) });

    await waitFor(() => expect(result.current.data?.check).toEqual({ verdict: 'ok' }), { timeout: 4000 });
    expect(api.get).toHaveBeenCalledWith('/voices/profiles/spec-010/takes/expert/1');
  });

  it('useUploadTake sube el WAV crudo a la ruta del estilo y refresca las tomas', async () => {
    api.upload.mockResolvedValue({ style: 'expert', take: 1, job: 4 });
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, 'invalidateQueries');
    const { result } = renderHook(() => useUploadTake('spec-010', 'expert'), { wrapper: wrapperWith(client) });
    const wav = new Uint8Array([82, 73, 70, 70]);

    await act(async () => {
      await result.current.mutateAsync(wav);
    });

    expect(api.upload).toHaveBeenCalledWith('/voices/profiles/spec-010/takes/expert', wav, 'audio/wav');
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['voices'] });
  });

  it('useChooseTake manda la toma a la referencia del estilo', async () => {
    api.post.mockResolvedValue({ style: 'expert', take: 2 });
    const { result } = renderHook(() => useChooseTake('spec-010', 'expert'), { wrapper: wrapperWith(new QueryClient()) });

    await act(async () => {
      await result.current.mutateAsync(2);
    });

    expect(api.post).toHaveBeenCalledWith('/voices/profiles/spec-010/takes/expert/2/choose');
  });
});

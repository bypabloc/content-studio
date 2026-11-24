import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EMPTY_FILTERS } from '@/features/library/query';
import { useAutoScan, useLibraryItems, useScan } from '@/features/library/useLibrary';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: new QueryClient({ defaultOptions: { queries: { retry: false } } }) }, children);

afterEach(() => vi.clearAllMocks());

describe('useLibrary (spec 020)', () => {
  it('pide la página con sus filtros y no pide nada en «Espacio»', async () => {
    api.get.mockResolvedValue({ items: [], total: 0 });
    const { result } = renderHook(() => useLibraryItems(EMPTY_FILTERS, { type: 'all' }, 1), { wrapper });
    renderHook(() => useLibraryItems(EMPTY_FILTERS, { type: 'storage' }, 1), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.get).toHaveBeenCalledTimes(1);
    expect(api.get).toHaveBeenCalledWith('/library?sort=date&page=1&page_size=200');
  });

  it('«Actualizar» encola el escaneo y sigue el trabajo hasta que termina', async () => {
    api.post.mockResolvedValue({ id: 9 });
    api.get.mockResolvedValueOnce({ status: 'running' }).mockResolvedValue({ status: 'done' });
    const { result } = renderHook(() => useScan(), { wrapper });

    act(() => result.current.refresh());

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/library/scan', {}));
    await waitFor(() => expect(result.current.scanning).toBe(false), { timeout: 4000 });
    expect(api.get).toHaveBeenCalledWith('/jobs/9');
  });

  it('al abrir escanea si el último escaneo es viejo o no hubo, y no si es reciente', async () => {
    const stale = vi.fn();
    const fresh = vi.fn();
    api.get.mockResolvedValueOnce({ value: '2000-01-01T00:00:00+00:00' });
    renderHook(() => useAutoScan(stale), { wrapper });
    await waitFor(() => expect(stale).toHaveBeenCalledTimes(1));

    api.get.mockResolvedValueOnce({ value: new Date().toISOString() });
    renderHook(() => useAutoScan(fresh), { wrapper });
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
    expect(fresh).not.toHaveBeenCalled();
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getLocale, setLocale } from '@/shared/i18n/locale';
import { useLanguage } from '@/shared/i18n/useLanguage';

const mocks = vi.hoisted(() => ({ fetch: vi.fn<typeof fetch>() }));

// La API se simula con el fetch de la prueba: `useApi` devuelve un cliente real apuntando a un server ficticio.
vi.mock('@/shared/api/context', async () => {
  const { createApi } = await import('@/shared/api/client');
  return { useApi: () => createApi({ baseUrl: 'http://127.0.0.1:9000', token: 'tok' }, mocks.fetch) };
});

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return createElement(QueryClientProvider, { client: queryClient }, children);
}

describe('useLanguage', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('ui.language', 'es');
    setLocale('es');
  });

  afterEach(() => {
    mocks.fetch.mockReset();
  });

  it('aplica al idioma activo la preferencia que guarda el server (ui.language)', async () => {
    mocks.fetch.mockResolvedValue(new Response(JSON.stringify({ key: 'ui.language', value: 'pt' })));

    renderHook(() => useLanguage(), { wrapper });

    await waitFor(() => expect(getLocale()).toBe('pt'));
  });

  it('sin preferencia del server, deja el idioma que ya estaba', async () => {
    mocks.fetch.mockResolvedValue(new Response(JSON.stringify({ key: 'ui.language', value: null })));

    renderHook(() => useLanguage(), { wrapper });

    await waitFor(() => expect(mocks.fetch).toHaveBeenCalled());
    expect(getLocale()).toBe('es');
  });
});

/** Lo común de las pruebas del asistente (spec 021): un fetch falso por ruta y el render con la API y la caché. */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import type { ReactElement, ReactNode } from 'react';
import { vi } from 'vitest';

import { ApiProvider } from '@/shared/api/context';

const connection = { baseUrl: 'http://api', token: 'tok' };
export const STATUS = {
  enabled: true,
  runtime_installed: true,
  selected: 'gemma-4-e4b',
  models: [{ model: 'gemma-4-e4b', size_gb: 5, vram_gb: 6, recommended: true, installed: true }],
  loaded: null,
  release_in: null,
};
type Route = unknown | ((body: unknown) => unknown);

/** Un fetch falso por ruta: «MÉTODO /ruta» o «/ruta»; lo que no está responde 404. */
export function api(routes: Record<string, Route>) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.replace(connection.baseUrl, '');
    const method = init?.method ?? 'GET';
    const route = routes[`${method} ${path}`] ?? routes[path];
    if (route === undefined) return new Response(JSON.stringify({ code: 'http.404' }), { status: 404 });
    const body = typeof route === 'function' ? (route as (body: unknown) => unknown)(init?.body ? JSON.parse(String(init.body)) : null) : route;
    return new Response(JSON.stringify(body), { status: 200 });
  });
}

/** El wrapper de la API y la caché, para \`renderHook\`. */
export function wrapperFor(fetchMock: ReturnType<typeof api>) {
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
}

export function renderWith(ui: ReactElement, fetchMock: ReturnType<typeof api>) {
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  return { ...render(ui, { wrapper }), queryClient };
}

export const calls = (fetchMock: ReturnType<typeof api>) =>
  fetchMock.mock.calls.map(([url, init]) => `${(init as RequestInit | undefined)?.method ?? 'GET'} ${String(url).replace(connection.baseUrl, '')}`);

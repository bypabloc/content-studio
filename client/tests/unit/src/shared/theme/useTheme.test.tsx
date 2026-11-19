import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiProvider } from '@/shared/api/context';
import { useTheme } from '@/shared/theme/useTheme';

const { setTheme } = vi.hoisted(() => ({ setTheme: vi.fn(async () => {}) }));
vi.mock('@tauri-apps/api/window', () => ({ getCurrentWindow: () => ({ setTheme }) }));

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function reply(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
}

const isDark = () => document.documentElement.classList.contains('dark');

describe('useTheme', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = '';
    fetchMock = vi.fn(async () => reply({ key: 'ui.theme', value: null }));
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sin preferencia en el server usa la caché para pintar', async () => {
    localStorage.setItem('ui.theme', 'dark');

    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current[0]).toBe('dark');
    expect(isDark()).toBe(true);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
  });

  it('la preferencia del server manda sobre la caché', async () => {
    localStorage.setItem('ui.theme', 'light');
    fetchMock.mockResolvedValue(reply({ key: 'ui.theme', value: 'dark' }));

    const { result } = renderHook(() => useTheme(), { wrapper });

    await waitFor(() => expect(result.current[0]).toBe('dark'));
    expect(isDark()).toBe(true);
  });

  it('dentro de Tauri avisa a la barra de la ventana: el modo, o null si es system', async () => {
    Object.defineProperty(window, '__TAURI_INTERNALS__', { value: {}, configurable: true });
    try {
      const { result } = renderHook(() => useTheme(), { wrapper });
      await waitFor(() => expect(setTheme).toHaveBeenLastCalledWith(null));
      fetchMock.mockResolvedValue(reply({ key: 'ui.theme', value: 'dark' }));

      act(() => result.current[1]('dark'));

      await waitFor(() => expect(setTheme).toHaveBeenLastCalledWith('dark'));
    } finally {
      Reflect.deleteProperty(window, '__TAURI_INTERNALS__');
    }
  });

  it('cambiar el tema hace PUT al server y actualiza la caché', async () => {
    const { result } = renderHook(() => useTheme(), { wrapper });
    fetchMock.mockResolvedValue(reply({ key: 'ui.theme', value: 'light' }));

    act(() => result.current[1]('light'));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/ui.theme',
        expect.objectContaining({ method: 'PUT', body: '{"value":"light"}' }),
      ),
    );
    expect(localStorage.getItem('ui.theme')).toBe('light');
    expect(isDark()).toBe(false);
  });
});

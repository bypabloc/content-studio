import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiProvider, useApi } from '@/shared/api/context';
import { tauriAlerts } from '@/shared/notify/alerts';

vi.mock('@/shared/notify/alerts', () => ({
  tauriAlerts: { toast: vi.fn(), system: vi.fn(), ding: vi.fn() },
}));

// El EventSource que abre ApiProvider: el test guarda la última conexión para emitir eventos a mano.
const live = vi.hoisted(() => ({ source: null as null | { emit(type: string, data: unknown): void } }));
class FakeEventSource {
  private readonly listeners = new Map<string, (event: { data: string }) => void>();

  constructor() {
    live.source = this;
  }

  addEventListener(type: string, listener: (event: { data: string }) => void) {
    this.listeners.set(type, listener);
  }

  close() {}

  emit(type: string, data: unknown) {
    this.listeners.get(type)?.({ data: JSON.stringify(data) });
  }
}

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

describe('ApiProvider y useApi', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('da el cliente de la API a los hijos', () => {
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={new QueryClient()}>
        <ApiProvider connection={connection}>{children}</ApiProvider>
      </QueryClientProvider>
    );

    const { result } = renderHook(() => useApi(), { wrapper });

    expect(typeof result.current.get).toBe('function');
  });

  it('useApi fuera de ApiProvider falla con un mensaje claro', () => {
    expect(() => renderHook(() => useApi())).toThrow('useApi must be used inside ApiProvider');
  });

  it('un trabajo que termina pasa por los avisos, con los ajustes de la caché', () => {
    vi.stubGlobal('EventSource', FakeEventSource);
    const queryClient = new QueryClient();
    queryClient.setQueryData(['settings', 'notify.system'], { key: 'notify.system', value: false });
    queryClient.setQueryData(['settings', 'notify.sound'], { key: 'notify.sound', value: false });
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        <ApiProvider connection={connection}>{children}</ApiProvider>
      </QueryClientProvider>
    );
    renderHook(() => null, { wrapper });

    live.source?.emit('job', {
      id: 5,
      kind: 'music',
      resource: 'gpu',
      status: 'done',
      position: 5,
      params: {},
      progress: 1,
      created_at: '2026-11-19T10:00:00Z',
    });

    expect(tauriAlerts.toast).toHaveBeenCalledWith(expect.objectContaining({ id: 5, status: 'done' }));
    expect(tauriAlerts.system).not.toHaveBeenCalled();
    expect(tauriAlerts.ding).not.toHaveBeenCalled();
  });
});

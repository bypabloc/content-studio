import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { LanPanel } from '@/features/settings/LanPanel';
import type { Connection } from '@/shared/api/client';
import { ApiProvider } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn(async (): Promise<unknown> => undefined) }));
vi.mock('@tauri-apps/api/core', () => ({ invoke }));

const connection: Connection = { baseUrl: 'http://127.0.0.1:41830', token: 'tok' };
const OFF = {
  enabled: false,
  address: null,
  port: 41831,
  max_upload_mb: 2048,
  keep_awake: true,
  running: false,
  url: null,
  addresses: ['192.168.1.20', '10.0.0.5'],
  fingerprint: null,
};
const ON = { ...OFF, enabled: true, address: '192.168.1.20', running: true, url: 'https://192.168.1.20:41831', fingerprint: 'AB:CD' };
const DEVICE = { id: 1, name: 'celular', scopes: ['jobs', 'files'], created_at: '2026-11-25T00:00:00+00:00', last_seen: null };

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

/** Responde la red local: los ajustes (que un PUT reemplaza por `afterPut`), los dispositivos y el PIN. */
function renderPanel(initial: unknown, devices: unknown[] = [], afterPut: unknown = ON) {
  let current = initial;
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/lan/settings') && init?.method === 'PUT') {
      current = afterPut;
      return json(current);
    }
    if (url.endsWith('/lan/settings')) return json(current);
    if (url.endsWith('/lan/devices')) return json(devices);
    if (url.endsWith('/lan/pairing')) return json({ pin: '123456', expires_in: 300 });
    if (url.includes('/lan/devices/') && init?.method === 'DELETE') return new Response(null, { status: 204 });
    return json({ key: '', value: null });
  });
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  render(<LanPanel />, { wrapper });
  return fetchMock;
}

function putBody(fetchMock: ReturnType<typeof vi.fn>) {
  const call = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith('/lan/settings') && init?.method === 'PUT');
  return call ? JSON.parse(String(call[1]?.body)) : undefined;
}

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  invoke.mockReset();
});

describe('LanPanel (spec 032, AC-10)', () => {
  it('activar abre el firewall para redes privadas y guarda la red local', async () => {
    const fetchMock = renderPanel(OFF);

    fireEvent.click(await screen.findByRole('switch', { name: t('settings.lan.enable') }));

    await waitFor(() => expect(putBody(fetchMock)).toEqual({ enabled: true, address: '192.168.1.20' }));
    expect(invoke).toHaveBeenCalledWith('set_lan_firewall', { enabled: true, port: 41831 });
    expect(await screen.findByText('https://192.168.1.20:41831')).toBeTruthy();
    expect(screen.getByText('AB:CD')).toBeTruthy();
  });

  it('si Windows no abre el puerto, avisa y la red local sigue apagada (AC-9)', async () => {
    invoke.mockRejectedValueOnce('firewall_declined');
    const fetchMock = renderPanel(OFF);

    fireEvent.click(await screen.findByRole('switch', { name: t('settings.lan.enable') }));

    expect(await screen.findByText(t('settings.lan.firewall_declined'))).toBeTruthy();
    expect(putBody(fetchMock)).toBeUndefined();
  });

  it('desactivar apaga la red local y borra la regla', async () => {
    const fetchMock = renderPanel(ON, [], OFF);

    fireEvent.click(await screen.findByRole('switch', { name: t('settings.lan.enable') }));

    await waitFor(() => expect(putBody(fetchMock)).toEqual({ enabled: false }));
    await waitFor(() => expect(invoke).toHaveBeenCalledWith('set_lan_firewall', { enabled: false, port: 41831 }));
  });

  it('emparejar muestra el PIN con su cuenta regresiva', async () => {
    // Solo el intervalo de la cuenta es falso: fetch y las esperas de Testing Library siguen con el reloj real.
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    renderPanel(ON);
    fireEvent.click(await screen.findByRole('button', { name: t('settings.lan.pair') }));
    expect(await screen.findByText(t('settings.lan.pin', { pin: '123456', seconds: 300 }))).toBeTruthy();

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(screen.getByText(t('settings.lan.pin', { pin: '123456', seconds: 299 }))).toBeTruthy();
    act(() => {
      vi.advanceTimersByTime(300_000);
    });
    expect(screen.queryByText(/123456/)).toBeNull();
  });

  it('revocar pide confirmación y borra el dispositivo', async () => {
    const fetchMock = renderPanel(ON, [DEVICE]);
    const confirm = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true);

    expect(await screen.findByText('celular')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('settings.lan.revoke') }));
    fireEvent.click(screen.getByRole('button', { name: t('settings.lan.revoke') }));

    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith('/lan/devices/1') && init?.method === 'DELETE')).toBe(true),
    );
    expect(confirm).toHaveBeenCalledTimes(2);
  });

  it('sin dispositivos lo dice, y sin activar la huella está pendiente', async () => {
    renderPanel(OFF);

    expect(await screen.findByText(t('settings.lan.no_devices'))).toBeTruthy();
    expect(screen.getByText(t('settings.lan.fingerprint_pending'))).toBeTruthy();
    expect(screen.getByText(t('settings.lan.warning'))).toBeTruthy();
  });

  it('un error de la API al guardar se muestra con su texto', async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/lan/settings') && init?.method === 'PUT') {
        return json({ code: 'lan_port_busy', params: { port: 41831 }, message: 'ocupado' }, 409);
      }
      if (url.endsWith('/lan/settings')) return json(OFF);
      return json([]);
    });
    vi.stubGlobal('fetch', fetchMock);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <ApiProvider connection={connection}>
          <LanPanel />
        </ApiProvider>
      </QueryClientProvider>,
    );

    fireEvent.click(await screen.findByRole('switch', { name: t('settings.lan.enable') }));

    expect(await screen.findByText(t('error.lan_port_busy', { port: 41831 }))).toBeTruthy();
  });
});

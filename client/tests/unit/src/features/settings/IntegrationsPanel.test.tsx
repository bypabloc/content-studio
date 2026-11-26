import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { IntegrationsPanel } from '@/features/settings/IntegrationsPanel';
import type { Connection } from '@/shared/api/client';
import { ApiProvider } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn(async () => undefined) }));
vi.mock('@tauri-apps/api/core', () => ({ invoke }));

const connection: Connection = { baseUrl: 'http://127.0.0.1:41830', token: 'tok' };

/** Responde a GET /settings/{key} con los valores dados (null si no hay); un PUT devuelve lo que se guardó. */
function settingsFetch(values: Record<string, unknown>) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const key = decodeURIComponent(url.split('/settings/')[1] ?? '');
    const value = init?.method === 'PUT' ? (JSON.parse(String(init.body)) as { value: unknown }).value : (values[key] ?? null);
    return new Response(JSON.stringify({ key, value }), { status: 200 });
  });
}

function renderPanel(reconnect?: () => Promise<Connection>) {
  const fetchMock = settingsFetch({ 'api.port': 41830, 'api.idle_minutes': 10 });
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection} reconnect={reconnect}>
        {children}
      </ApiProvider>
    </QueryClientProvider>
  );
  return { fetchMock, ...render(<IntegrationsPanel />, { wrapper }) };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  invoke.mockClear();
});

describe('IntegrationsPanel (spec 028, AC-11)', () => {
  it('muestra la dirección, el puerto y los minutos de inactividad', async () => {
    renderPanel();

    expect(screen.getByText(connection.baseUrl)).toBeTruthy();
    expect(await screen.findByDisplayValue('41830')).toBeTruthy();
    expect(await screen.findByText(t('settings.integrations.idle', { minutes: 10 }))).toBeTruthy();
  });

  it('cambiar el puerto y los minutos guarda cada ajuste', async () => {
    const { fetchMock } = renderPanel();

    fireEvent.change(await screen.findByDisplayValue('41830'), { target: { value: '41900' } });
    fireEvent.change(await screen.findByDisplayValue('10'), { target: { value: '15' } });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `${connection.baseUrl}/settings/api.port`,
        expect.objectContaining({ method: 'PUT', body: JSON.stringify({ value: 41900 }) }),
      );
      expect(fetchMock).toHaveBeenCalledWith(
        `${connection.baseUrl}/settings/api.idle_minutes`,
        expect.objectContaining({ method: 'PUT', body: JSON.stringify({ value: 15 }) }),
      );
    });
  });

  it('«Copiar token» copia el token de la conexión', async () => {
    const writeText = vi.fn(async () => undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    renderPanel();

    fireEvent.click(await screen.findByRole('button', { name: t('settings.integrations.copy_token') }));

    expect(writeText).toHaveBeenCalledWith('tok');
  });

  it('«Cambiar token» pide confirmación: sin confirmar no cambia nada', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderPanel();

    fireEvent.click(await screen.findByRole('button', { name: t('settings.integrations.rotate_token') }));

    expect(confirm).toHaveBeenCalledWith(t('settings.integrations.rotate_confirm'));
    expect(invoke).not.toHaveBeenCalledWith('rotate_token');
  });

  it('con confirmación, cambia el token y pide la conexión otra vez', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const reconnect = vi.fn(async () => connection);
    renderPanel(reconnect);

    fireEvent.click(await screen.findByRole('button', { name: t('settings.integrations.rotate_token') }));

    await waitFor(() => expect(reconnect).toHaveBeenCalledOnce());
    expect(invoke).toHaveBeenCalledWith('rotate_token');
  });

  it('si el server no puede cambiar el token, lo dice y no se reconecta', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    invoke.mockRejectedValueOnce('server_exited');
    const reconnect = vi.fn(async () => connection);
    renderPanel(reconnect);

    fireEvent.click(await screen.findByRole('button', { name: t('settings.integrations.rotate_token') }));

    expect(await screen.findByText(t('settings.integrations.rotate_failed'))).toBeTruthy();
    expect(reconnect).not.toHaveBeenCalled();
  });
});

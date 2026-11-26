import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { InboxFolders } from '@/features/settings/InboxFolders';
import type { Connection } from '@/shared/api/client';
import { ApiProvider } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

const { open } = vi.hoisted(() => ({ open: vi.fn(async (): Promise<string | null> => '/entrada') }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

const connection: Connection = { baseUrl: 'http://127.0.0.1:41830', token: 'tok' };
const FOLDER = {
  id: 1,
  path: '/musica/entrada',
  kind: 'media.convert',
  params: { target: 'mp3' },
  keep_awake: true,
  paused: false,
  created_at: '2026-11-25T00:00:00+00:00',
};

/** El cuerpo JSON del primer POST cuya ruta termina en `suffix`, o undefined si no hubo. */
function bodyOf(fetchMock: ReturnType<typeof vi.fn>, suffix: string) {
  const call = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith(suffix) && init?.method === 'POST');
  return call ? JSON.parse(String(call[1]?.body)) : undefined;
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

/** Responde las carpetas de entrada; un POST usa `post`. Los ajustes de avisos que pide la app van con un valor nulo. */
function renderFolders(folders: unknown[], post: () => Response = () => json(FOLDER, 201)) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/inbox/folders') && init?.method === 'POST') return post();
    if (url.includes('/inbox/folders')) return json(folders);
    return json({ key: '', value: null });
  });
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  render(<InboxFolders />, { wrapper });
  return fetchMock;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('InboxFolders (spec 030, AC-9)', () => {
  it('lista las carpetas registradas y si están pausadas', async () => {
    renderFolders([{ ...FOLDER, paused: true }]);

    expect(await screen.findByText('/musica/entrada')).toBeTruthy();
    expect(screen.getByText(t('settings.inbox.paused'))).toBeTruthy();
  });

  it('agrega una carpeta con convertir a MP3 y con keep_awake activo por defecto', async () => {
    const fetchMock = renderFolders([]);
    expect(await screen.findByText(t('settings.inbox.empty'))).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: t('settings.inbox.pick') }));
    expect(await screen.findByText('/entrada')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('settings.inbox.add') }));

    await waitFor(() => {
      const post = fetchMock.mock.calls.find(([url, init]) => url.endsWith('/inbox/folders') && init?.method === 'POST');
      expect(JSON.parse(String(post?.[1]?.body))).toEqual({
        path: '/entrada',
        kind: 'media.convert',
        params: { target: 'mp3' },
        keep_awake: true,
      });
    });
  });

  it('muestra el texto del catálogo cuando la API no acepta la carpeta', async () => {
    renderFolders([], () =>
      json({ code: 'inbox_path_not_found', params: { path: '/entrada' }, message: 'No existe la carpeta /entrada.' }, 422),
    );

    fireEvent.click(screen.getByRole('button', { name: t('settings.inbox.pick') }));
    await screen.findByText('/entrada');
    fireEvent.click(screen.getByRole('button', { name: t('settings.inbox.add') }));

    expect(await screen.findByText(t('error.inbox_path_not_found', { path: '/entrada' }))).toBeTruthy();
  });

  it('pausa una carpeta con su botón', async () => {
    const fetchMock = renderFolders([FOLDER]);

    fireEvent.click(await screen.findByRole('button', { name: t('settings.inbox.pause') }));

    await waitFor(() => expect(bodyOf(fetchMock, '/inbox/folders/1/pause')).toEqual({ paused: true }));
  });

  it('quita una carpeta solo si se confirma', async () => {
    const fetchMock = renderFolders([FOLDER]);
    const confirm = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true);

    fireEvent.click(await screen.findByRole('button', { name: t('settings.inbox.remove') }));
    fireEvent.click(screen.getByRole('button', { name: t('settings.inbox.remove') }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith('/inbox/folders/1') && init?.method === 'DELETE')).toBe(true));
    expect(confirm).toHaveBeenCalledTimes(2);
  });

  it('apaga keep_awake con el interruptor antes de agregar', async () => {
    const fetchMock = renderFolders([]);

    fireEvent.click(await screen.findByRole('switch', { name: t('settings.inbox.keep_awake') }));
    fireEvent.click(screen.getByRole('button', { name: t('settings.inbox.pick') }));
    await screen.findByText('/entrada');
    fireEvent.click(screen.getByRole('button', { name: t('settings.inbox.add') }));

    await waitFor(() => expect(bodyOf(fetchMock, '/inbox/folders')).toMatchObject({ keep_awake: false }));
  });

  it('no cambia la carpeta si el diálogo se cancela', async () => {
    open.mockResolvedValueOnce(null);
    renderFolders([]);

    fireEvent.click(await screen.findByRole('button', { name: t('settings.inbox.pick') }));

    await waitFor(() => expect(open).toHaveBeenCalled());
    expect(screen.queryByText('/entrada')).toBeNull();
  });
});

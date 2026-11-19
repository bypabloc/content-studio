import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SettingsPage } from '@/features/settings/SettingsPage';
import { ApiProvider } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function reply(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

function renderPage(fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  return render(<SettingsPage />, { wrapper });
}

const requests = (fetchMock: ReturnType<typeof vi.fn>) =>
  fetchMock.mock.calls.map(([url, init]) => `${(init as RequestInit | undefined)?.method ?? 'GET'} ${url}`);

describe('SettingsPage', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    localStorage.clear();
    fetchMock = vi.fn(async (_url: string, init?: RequestInit) =>
      init?.method === 'DELETE' ? reply({ deleted: 2 }) : reply({ key: 'x', value: null }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('el campo de tema guarda la elección en ui.theme', async () => {
    renderPage(fetchMock);

    fireEvent.change(screen.getByLabelText(t('settings.theme')), { target: { value: 'dark' } });

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/ui.theme',
        expect.objectContaining({ method: 'PUT', body: '{"value":"dark"}' }),
      ),
    );
  });

  it('los avisos se apagan por separado, cada uno en su ajuste', async () => {
    renderPage(fetchMock);

    fireEvent.click(screen.getByLabelText(t('settings.notify_sound')));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/notify.sound',
        expect.objectContaining({ method: 'PUT', body: '{"value":false}' }),
      ),
    );
  });

  it('restablecer pide confirmación y borra solo los selectores; el tema y los avisos se quedan', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPage(fetchMock);

    fireEvent.click(screen.getByRole('button', { name: t('settings.reset') }));

    await waitFor(() => expect(requests(fetchMock)).toContain('DELETE http://127.0.0.1:9000/settings?prefix=select.'));
    expect(requests(fetchMock).some((request) => request.includes('ui.theme') && request.startsWith('DELETE'))).toBe(
      false,
    );
  });

  it('si se cancela la confirmación, no se borra nada', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderPage(fetchMock);

    fireEvent.click(screen.getByRole('button', { name: t('settings.reset') }));

    expect(requests(fetchMock).some((request) => request.startsWith('DELETE'))).toBe(false);
  });
});

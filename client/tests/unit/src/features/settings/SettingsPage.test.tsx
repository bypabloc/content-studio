import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

// El selector es un combobox (UISelect sobre Base UI): se abre y se elige la opción por su nombre.
async function choose(name: string, option: string): Promise<void> {
  await userEvent.click(await screen.findByRole('combobox', { name }));
  await userEvent.click(await screen.findByRole('option', { name: option }));
}

describe('SettingsPage', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // El idioma en caché es español: sin él, «system» en jsdom (en-US) daría inglés.
    localStorage.clear();
    localStorage.setItem('ui.language', 'es');
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

    await choose(t('settings.theme'), t('theme.dark'));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/ui.theme',
        expect.objectContaining({ method: 'PUT', body: '{"value":"dark"}' }),
      ),
    );
  });

  it('el idioma tiene ★ en Sistema y guarda la elección en ui.language (AC-8)', async () => {
    renderPage(fetchMock);

    await userEvent.click(await screen.findByRole('combobox', { name: t('settings.language') }));
    expect(await screen.findByRole('option', { name: `★ ${t('language.system')}` })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Português' })).toBeTruthy();

    await userEvent.click(screen.getByRole('option', { name: t('language.en') }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/ui.language',
        expect.objectContaining({ method: 'PUT', body: '{"value":"en"}' }),
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

  it('el selector de tema muestra el ícono de cada opción (spec 009, D-5)', async () => {
    renderPage(fetchMock);

    await userEvent.click(await screen.findByRole('combobox', { name: t('settings.theme') }));

    expect(screen.getByRole('option', { name: t('theme.light') }).querySelector('svg.lucide-sun')).not.toBeNull();
    expect(screen.getByRole('option', { name: t('theme.dark') }).querySelector('svg.lucide-moon')).not.toBeNull();
    expect(screen.getByRole('option', { name: t('theme.system') }).querySelector('svg.lucide-monitor')).not.toBeNull();
  });

  it('restablecer lleva su ícono y su texto (spec 009, D-5)', () => {
    renderPage(fetchMock);

    const reset = screen.getByRole('button', { name: t('settings.reset') });
    expect(reset.textContent).toBe(t('settings.reset'));
    expect(reset.querySelector('svg.lucide-rotate-ccw-clock')).not.toBeNull();
  });

  it('si se cancela la confirmación, no se borra nada', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderPage(fetchMock);

    fireEvent.click(screen.getByRole('button', { name: t('settings.reset') }));

    expect(requests(fetchMock).some((request) => request.startsWith('DELETE'))).toBe(false);
  });
});

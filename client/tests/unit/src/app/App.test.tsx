import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { invoke } from '@tauri-apps/api/core';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App, APP_VERSION } from '@/app/App';
import { t } from '@/shared/i18n/t';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn() }));
vi.mock('@tauri-apps/api/event', () => ({ listen: vi.fn(async () => () => {}) }));
const invokeMock = vi.mocked(invoke);
const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function reply(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

describe('App', () => {
  beforeEach(() => {
    invokeMock.mockReset();
    // La app lee la preferencia de tema del server al montar la pantalla principal.
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => reply({ key: 'ui.theme', value: null })),
    );
  });

  // Sin globals de vitest, RTL no limpia el DOM entre tests.
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.location.hash = '';
  });

  it('con el server arriba muestra la navegación con el nombre y la versión', async () => {
    invokeMock.mockResolvedValue(connection);

    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Content Studio' })).toBeTruthy();
    expect(screen.getByText(`Versión ${APP_VERSION}`)).toBeTruthy();
    expect(screen.getByRole('link', { name: t('nav.settings') })).toBeTruthy();
    expect(invokeMock).toHaveBeenCalledWith('get_connection');
  });

  it('con una sección en el hash la muestra como título', async () => {
    window.location.hash = '#/settings';
    invokeMock.mockResolvedValue(connection);

    render(<App />);

    // "Ajustes" es también el título del grupo en la sidebar: se busca dentro del área principal.
    await screen.findByRole('heading', { name: 'Content Studio' });
    expect(within(screen.getByRole('main')).getByRole('heading', { level: 2, name: t('nav.settings') })).toBeTruthy();
  });

  it.each([
    ['server_spawn_failed', 'server.spawn_failed'],
    ['server_exited', 'server.exited'],
  ] as const)('explica el código %s', async (code, key) => {
    invokeMock.mockRejectedValueOnce(code);

    render(<App />);

    expect(await screen.findByText(t(key))).toBeTruthy();
  });

  it('si el server no arranca muestra el motivo y Reintentar, que vuelve a pedir la conexión', async () => {
    invokeMock.mockRejectedValueOnce('server_timeout');
    invokeMock.mockResolvedValueOnce(connection);

    render(<App />);
    expect(await screen.findByText(t('server.timeout'))).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: t('server.retry') }));

    expect(await screen.findByRole('heading', { name: 'Content Studio' })).toBeTruthy();
    expect(invokeMock).toHaveBeenCalledTimes(2);
  });

  it('si falla la preparación de la app instalada muestra el paso y Reintentar vuelve a prepararla', async () => {
    invokeMock.mockRejectedValueOnce('bootstrap_sync_failed');
    invokeMock.mockResolvedValueOnce(connection);

    render(<App />);
    expect(await screen.findByText(t('bootstrap.error.sync'))).toBeTruthy();
    expect(screen.getByRole('heading', { name: t('bootstrap.title') })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('server.retry') }));

    expect(await screen.findByRole('heading', { name: 'Content Studio' })).toBeTruthy();
    expect(invokeMock).toHaveBeenCalledTimes(2);
  });
});

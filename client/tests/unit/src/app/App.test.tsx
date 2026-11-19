import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { invoke } from '@tauri-apps/api/core';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App, APP_VERSION } from '@/app/App';
import { t } from '@/shared/i18n/t';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn() }));
const invokeMock = vi.mocked(invoke);
const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

describe('App', () => {
  beforeEach(() => {
    invokeMock.mockReset();
  });

  // Sin globals de vitest, RTL no limpia el DOM entre tests.
  afterEach(() => {
    cleanup();
  });

  it('con el server arriba muestra el nombre y la versión', async () => {
    invokeMock.mockResolvedValue(connection);

    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Content Studio' })).toBeTruthy();
    expect(screen.getByText(`Versión ${APP_VERSION}`)).toBeTruthy();
    expect(invokeMock).toHaveBeenCalledWith('get_connection');
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
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/core';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { StartAtLogin } from '@/features/settings/StartAtLogin';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';

vi.mock('@tauri-apps/api/core', () => ({ invoke: vi.fn() }));
vi.mock('@/shared/components/molecules/UIToast', () => ({ toast: { error: vi.fn(), info: vi.fn() } }));

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => ({ key: path.replace('/settings/', ''), value: null }));
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({ key: path, value: body.value }));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderToggle() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <StartAtLogin />
    </QueryClientProvider>,
  );
}

describe('StartAtLogin (spec 031, AC-8)', () => {
  it('AC-8: WHEN se activa el inicio THEN el comando de la app recibe true y el ajuste se guarda', async () => {
    vi.mocked(invoke).mockResolvedValue(undefined);
    renderToggle();
    const user = userEvent.setup();
    await user.click(await screen.findByRole('checkbox', { name: t('settings.system.start_at_login') }));
    await waitFor(() => expect(invoke).toHaveBeenCalledWith('set_start_at_login', { enabled: true }));
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/system.start_at_login', { value: true }));
  });

  it('WHEN el comando falla THEN avisa y el ajuste no cambia', async () => {
    vi.mocked(invoke).mockRejectedValue('solo en la app instalada');
    renderToggle();
    const user = userEvent.setup();
    await user.click(await screen.findByRole('checkbox', { name: t('settings.system.start_at_login') }));
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith(t('settings.system.start_at_login_error')));
    expect(api.put).not.toHaveBeenCalled();
  });
});

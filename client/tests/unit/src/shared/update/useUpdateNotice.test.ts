import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ComponentProps, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiProvider } from '@/shared/api/context';
import { toast } from '@/shared/components/molecules/UIToast';
import { t } from '@/shared/i18n/t';
import { useUpdateNotice } from '@/shared/update/useUpdateNotice';
import type { UpdaterDeps } from '@/shared/update/useUpdater';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function setup(deps: UpdaterDeps, jobs = '[]') {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(jobs, { status: 200 })));
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, createElement(ApiProvider, { connection } as ComponentProps<typeof ApiProvider>, children));
  return renderHook(() => useUpdateNotice(deps), { wrapper });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('useUpdateNotice (spec 022, D-6)', () => {
  it('AC-9: al abrir busca y, con una versión nueva, deja un aviso fijo con «Actualizar y reiniciar»', async () => {
    const info = vi.spyOn(toast, 'info').mockImplementation(() => {});
    const check = vi.fn(async () => ({ version: '0.1.1', downloadAndInstall: vi.fn(async () => {}) }));

    setup({ check, relaunch: vi.fn(async () => {}) });

    await waitFor(() => expect(info).toHaveBeenCalledOnce());
    expect(check).toHaveBeenCalledOnce();
    const [message, options] = info.mock.calls[0];
    expect(message).toBe(t('update.available', { version: '0.1.1' }));
    expect(options).toMatchObject({ persistent: true, action: { label: t('update.install') } });
  });

  it('sin versión nueva, o sin poder buscar, no avisa nada', async () => {
    const info = vi.spyOn(toast, 'info').mockImplementation(() => {});
    const check = vi.fn(async () => Promise.reject(new Error('offline')));

    setup({ check, relaunch: vi.fn(async () => {}) });

    await waitFor(() => expect(check).toHaveBeenCalledOnce());
    expect(info).not.toHaveBeenCalled();
  });

  it('AC-9: al aceptar con un trabajo corriendo, avisa que espera a que termine', async () => {
    const info = vi.spyOn(toast, 'info').mockImplementation(() => {});
    const check = vi.fn(async () => ({ version: '0.1.1', downloadAndInstall: vi.fn(async () => {}) }));

    setup({ check, relaunch: vi.fn(async () => {}) }, JSON.stringify([{ id: 1, status: 'running' }]));
    await waitFor(() => expect(info).toHaveBeenCalledOnce());
    const options = info.mock.calls[0][1] as { action: { onClick: () => void } };
    act(() => options.action.onClick());

    await waitFor(() => expect(info).toHaveBeenCalledTimes(2));
    expect(info.mock.calls[1][0]).toBe(t('update.waiting', { count: 1 }));
  });
});

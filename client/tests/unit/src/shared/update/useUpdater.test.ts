import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ComponentProps, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiProvider } from '@/shared/api/context';
import type { Job } from '@/shared/api/events';
import { updateMessage, useUpdater, type UpdaterDeps } from '@/shared/update/useUpdater';
import { t } from '@/shared/i18n/t';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function setup(deps: UpdaterDeps, jobs: Partial<Job>[] = []) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(jobs), { status: 200 })));
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, createElement(ApiProvider, { connection } as ComponentProps<typeof ApiProvider>, children));
  return { queryClient, ...renderHook(() => useUpdater(deps), { wrapper }) };
}

function fakeDeps(version: string | null) {
  const downloadAndInstall = vi.fn(async () => {});
  const relaunch = vi.fn(async () => {});
  const check = vi.fn(async () => (version ? { version, downloadAndInstall } : null));
  return { deps: { check, relaunch }, downloadAndInstall, relaunch, check };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useUpdater (spec 022, AC-9)', () => {
  it('sin versión nueva queda en «latest» y no instala nada', async () => {
    const { deps, downloadAndInstall } = fakeDeps(null);
    const { result } = setup(deps);

    await act(async () => {
      await result.current.check();
    });

    expect(result.current.state).toEqual({ kind: 'latest' });
    expect(downloadAndInstall).not.toHaveBeenCalled();
  });

  it('AC-9: con una versión nueva la ofrece; al aceptar, instala y reinicia', async () => {
    const { deps, downloadAndInstall, relaunch } = fakeDeps('0.1.1');
    const { result } = setup(deps);

    await act(async () => {
      await result.current.check();
    });
    expect(result.current.state).toEqual({ kind: 'available', version: '0.1.1' });

    act(() => result.current.install());

    await waitFor(() => expect(relaunch).toHaveBeenCalledOnce());
    expect(downloadAndInstall).toHaveBeenCalledOnce();
  });

  it('AC-9: con un trabajo corriendo espera a que termine antes de instalar', async () => {
    const { deps, downloadAndInstall, relaunch } = fakeDeps('0.1.1');
    const { result, queryClient } = setup(deps, [{ id: 7, status: 'running' }]);
    await waitFor(() => expect(result.current.running).toBe(1));

    await act(async () => {
      await result.current.check();
    });
    act(() => result.current.install());

    expect(result.current.state).toEqual({ kind: 'waiting', version: '0.1.1' });
    expect(downloadAndInstall).not.toHaveBeenCalled();

    act(() => queryClient.setQueryData<Partial<Job>[]>(['jobs'], [{ id: 7, status: 'done' }]));

    await waitFor(() => expect(relaunch).toHaveBeenCalledOnce());
    expect(downloadAndInstall).toHaveBeenCalledOnce();
  });

  it('si la consulta o la instalación fallan, queda en «failed» sin reiniciar', async () => {
    const { deps, relaunch } = fakeDeps('0.1.1');
    deps.check.mockRejectedValueOnce(new Error('offline'));
    const { result } = setup(deps);

    await act(async () => {
      await result.current.check();
    });
    expect(result.current.state).toEqual({ kind: 'failed' });

    const broken = { version: '0.1.1', downloadAndInstall: vi.fn(async () => Promise.reject(new Error('bad signature'))) };
    deps.check.mockResolvedValueOnce(broken);
    await act(async () => {
      await result.current.check();
    });
    act(() => result.current.install());

    await waitFor(() => expect(result.current.state).toEqual({ kind: 'failed' }));
    expect(relaunch).not.toHaveBeenCalled();
  });

  it('cada estado tiene su texto, salvo el inicial', () => {
    expect(updateMessage({ kind: 'idle' }, 0)).toBeNull();
    expect(updateMessage({ kind: 'checking' }, 0)).toBe(t('update.checking'));
    expect(updateMessage({ kind: 'waiting', version: '1.0.0' }, 2)).toBe(t('update.waiting', { count: 2 }));
    expect(updateMessage({ kind: 'installing', version: '1.0.0' }, 0)).toBe(t('update.installing', { version: '1.0.0' }));
  });
});

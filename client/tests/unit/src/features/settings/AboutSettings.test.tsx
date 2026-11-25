import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { APP_VERSION } from '@/shared/version';
import { openUrl } from '@tauri-apps/plugin-opener';
import { AboutSettings } from '@/features/settings/AboutSettings';
import { ApiProvider } from '@/shared/api/context';
import { t } from '@/shared/i18n/t';
import type { UpdaterDeps } from '@/shared/update/useUpdater';

vi.mock('@tauri-apps/plugin-opener', () => ({ openUrl: vi.fn() }));

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function renderAbout(deps: UpdaterDeps) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response('[]', { status: 200 })));
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  return render(<AboutSettings deps={deps} />, { wrapper });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('AboutSettings (spec 022, D-6)', () => {
  it('muestra la versión y, al buscar sin novedades, dice que es la última', async () => {
    renderAbout({ check: vi.fn(async () => null), relaunch: vi.fn() });

    expect(screen.getByText(t('app.version', { version: APP_VERSION }))).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: t('update.check') }));

    expect(await screen.findByText(t('update.latest'))).toBeTruthy();
  });

  it('AC-9: con una versión nueva ofrece «Actualizar y reiniciar» y lo hace', async () => {
    const downloadAndInstall = vi.fn(async () => {});
    const relaunch = vi.fn(async () => {});
    renderAbout({ check: vi.fn(async () => ({ version: '9.9.9', downloadAndInstall })), relaunch });

    await userEvent.click(screen.getByRole('button', { name: t('update.check') }));
    expect(await screen.findByText(t('update.available', { version: '9.9.9' }))).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: t('update.install') }));

    await waitFor(() => expect(relaunch).toHaveBeenCalledOnce());
    expect(downloadAndInstall).toHaveBeenCalledOnce();
  });

  it('si no puede buscar, lo dice', async () => {
    renderAbout({ check: vi.fn(async () => Promise.reject(new Error('offline'))), relaunch: vi.fn() });

    await userEvent.click(screen.getByRole('button', { name: t('update.check') }));

    expect(await screen.findByText(t('update.failed'))).toBeTruthy();
  });

  it('AC-6: Acerca de muestra la atribución de community-1 con su enlace', () => {
    renderAbout({ check: vi.fn(async () => null), relaunch: vi.fn() });

    expect(screen.getByText(/CC BY 4\.0/)).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Modelo en Hugging Face' })).toBeTruthy();
  });

  it('AC-6: el enlace de Acerca de abre el modelo en el navegador', async () => {
    renderAbout({ check: vi.fn(async () => null), relaunch: vi.fn() });

    await userEvent.click(screen.getByRole('link', { name: 'Modelo en Hugging Face' }));

    expect(openUrl).toHaveBeenCalledWith('https://huggingface.co/pyannote/speaker-diarization-community-1');
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ApiProvider } from '@/shared/api/context';
import { UIWhisperModelSelect } from '@/shared/components/molecules/UIWhisperModelSelect';
import { t } from '@/shared/i18n/t';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };
const engines = [
  {
    engine: 'faster-whisper',
    models: [
      { model: 'small', size_gb: 0.5, vram_gb: 1, recommended: false, downloaded: false },
      { model: 'medium', size_gb: 1.5, vram_gb: 2, recommended: false, downloaded: false },
      { model: 'large-v3-turbo', size_gb: 1.6, vram_gb: 3, recommended: true, downloaded: true },
    ],
  },
];

function reply(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

// Un cliente nuevo por montaje: al volver a montar, la preferencia se pide de nuevo al server.
function mount(saved: string | null) {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/engines')) return reply(engines);
    if (init?.method === 'PUT') return reply({ key: 'select.whisper.model', value: JSON.parse(String(init.body)).value });
    return reply({ key: 'select.whisper.model', value: saved });
  });
  vi.stubGlobal('fetch', fetchMock);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ApiProvider connection={connection}>{children}</ApiProvider>
    </QueryClientProvider>
  );
  const result = render(<UIWhisperModelSelect />, { wrapper });
  return { ...result, fetchMock };
}

async function combobox(): Promise<HTMLInputElement> {
  return (await screen.findByRole('combobox', { name: t('whisper.model') })) as HTMLInputElement;
}

describe('UIWhisperModelSelect (spec 013, D-1, AC-9)', () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  // El primer test de cada archivo paga el arranque en frío del selector (carga perezosa): por eso su tiempo es mayor.
  it('AC-9: sin elección guardada preselecciona large-v3-turbo, con la estrella', async () => {
    mount(null);

    await waitFor(async () => expect((await combobox()).value).toBe('★ large-v3-turbo'));
  }, 20_000);

  it('AC-9: muestra el tamaño de cada modelo y avisa cuando falta su descarga', async () => {
    mount(null);
    await waitFor(async () => expect((await combobox()).value).toBe('★ large-v3-turbo'));

    await userEvent.click(await combobox());

    expect(screen.getByRole('option', { name: /medium/ }).textContent).toContain('1.5 GB');
    expect(screen.getByRole('option', { name: /medium/ }).textContent).toContain(t('whisper.not_downloaded'));
    expect(screen.getByRole('option', { name: /large-v3-turbo/ }).textContent).toContain(t('whisper.downloaded'));
  });

  it('AC-9: al elegir medium la guarda; al volver a montar queda preseleccionada y la estrella sigue en large-v3-turbo', async () => {
    const first = mount(null);
    await waitFor(async () => expect((await combobox()).value).toBe('★ large-v3-turbo'));
    await userEvent.click(await combobox());
    await userEvent.click(screen.getByRole('option', { name: /medium/ }));

    await waitFor(() =>
      expect(first.fetchMock).toHaveBeenCalledWith(
        'http://127.0.0.1:9000/settings/select.whisper.model',
        expect.objectContaining({ method: 'PUT', body: '{"value":"medium"}' }),
      ),
    );
    first.unmount();

    mount('medium');

    await waitFor(async () => expect((await combobox()).value).toBe('medium'));
    await userEvent.click(await combobox());
    expect(screen.getByRole('option', { name: /large-v3-turbo/ }).textContent).toContain('★');
  });
});

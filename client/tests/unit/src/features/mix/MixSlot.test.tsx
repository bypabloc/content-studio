import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MixSlot } from '@/features/mix/MixSlot';
import { t } from '@/shared/i18n/t';

const { api, open } = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(), fileUrl: (path: string) => `file://${path}` },
  open: vi.fn(),
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

function renderSlot(onPick: (path: string) => void, value: string | null = null) {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MixSlot slot="voice" value={value} onPick={onPick} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  api.get.mockImplementation(async (path: string) =>
    path.startsWith('/jobs?')
      ? [{ id: 5, kind: 'narration', status: 'done', starred: false, params: {}, output_dir: 'out/a' }]
      : ['out/a/script.json', 'out/a/voz.wav'],
  );
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('MixSlot (spec 016, D-4)', () => {
  it('muestra la ruta elegida, o «Sin archivo» si la ranura está vacía', () => {
    const { unmount } = renderSlot(vi.fn());

    expect(screen.getByText(t('mix.slot.empty'))).toBeTruthy();
    unmount();
    renderSlot(vi.fn(), 'D:/media/voz.wav');

    expect(screen.getByText('D:/media/voz.wav')).toBeTruthy();
  });

  it('«Archivo…» manda la ruta que elige el diálogo', async () => {
    open.mockResolvedValueOnce('D:/media/voz.wav');
    const onPick = vi.fn();
    renderSlot(onPick);

    await userEvent.click(screen.getByRole('button', { name: t('mix.source.file') }));

    await waitFor(() => expect(onPick).toHaveBeenCalledWith('D:/media/voz.wav'));
  });

  it('«Del historial» toma el primer audio del trabajo que elige', async () => {
    const onPick = vi.fn();
    renderSlot(onPick);

    await userEvent.click(await screen.findByRole('combobox', { name: t('mix.source.history') }));
    await userEvent.click(await screen.findByRole('option', { name: /narration #5/ }));

    await waitFor(() => expect(onPick).toHaveBeenCalledWith('out/a/voz.wav'));
  });

  it('cancelar el diálogo no cambia la ranura', async () => {
    open.mockResolvedValueOnce(null);
    const onPick = vi.fn();
    renderSlot(onPick);

    await userEvent.click(screen.getByRole('button', { name: t('mix.source.file') }));

    await waitFor(() => expect(open).toHaveBeenCalled());
    expect(onPick).not.toHaveBeenCalled();
  });

  it('un trabajo sin audio no elige nada', async () => {
    api.get.mockImplementation(async (path: string) =>
      path.startsWith('/jobs?')
        ? [{ id: 5, kind: 'narration', status: 'done', starred: false, params: {}, output_dir: 'out/a' }]
        : ['out/a/script.json'],
    );
    const onPick = vi.fn();
    renderSlot(onPick);

    await userEvent.click(await screen.findByRole('combobox', { name: t('mix.source.history') }));
    await userEvent.click(await screen.findByRole('option', { name: /narration #5/ }));

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/jobs/5/outputs'));
    expect(onPick).not.toHaveBeenCalled();
  });
});

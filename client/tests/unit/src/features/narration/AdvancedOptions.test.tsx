import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AdvancedOptions } from '@/features/narration/AdvancedOptions';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => ({ key: path.replace('/settings/', ''), value: null }));
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({
    key: path.replace('/settings/', ''),
    value: body.value,
  }));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderAdvanced(supportsBatch: boolean) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <AdvancedOptions supportsBatch={supportsBatch} />
    </QueryClientProvider>,
  );
}

describe('AdvancedOptions', () => {
  it('el lote solo aparece si el motor lo admite', () => {
    const first = renderAdvanced(false);
    expect(screen.queryByRole('spinbutton', { name: t('narration.advanced.batch') })).toBeNull();
    first.unmount();

    renderAdvanced(true);
    expect(screen.getByRole('spinbutton', { name: t('narration.advanced.batch') })).toBeTruthy();
  });

  it('una semilla escrita se guarda como número, y vaciarla la deja en null (aleatoria)', async () => {
    renderAdvanced(false);
    const seed = screen.getByRole('spinbutton', { name: t('narration.advanced.seed') });

    fireEvent.change(seed, { target: { value: '7' } });
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/narration.seed', { value: 7 }));

    fireEvent.change(seed, { target: { value: '' } });
    await waitFor(() => expect(api.put).toHaveBeenLastCalledWith('/settings/narration.seed', { value: null }));
  });

  it('el lote y los reintentos se guardan como números', async () => {
    renderAdvanced(true);

    fireEvent.change(screen.getByRole('spinbutton', { name: t('narration.advanced.batch') }), {
      target: { value: '4' },
    });
    fireEvent.change(screen.getByRole('spinbutton', { name: t('narration.advanced.retries') }), {
      target: { value: '2' },
    });

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/narration.batch', { value: 4 }));
    expect(api.put).toHaveBeenCalledWith('/settings/narration.retries', { value: 2 });
  });

  it('la masterización, los LUFS y la evaluación se guardan como se eligieron', async () => {
    renderAdvanced(false);

    fireEvent.change(screen.getByRole('combobox', { name: t('narration.advanced.master') }), {
      target: { value: 'no' },
    });
    fireEvent.change(screen.getByRole('spinbutton', { name: t('narration.advanced.lufs') }), {
      target: { value: '-14' },
    });
    fireEvent.click(screen.getByRole('checkbox'));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/narration.master', { value: 'no' }));
    expect(api.put).toHaveBeenCalledWith('/settings/narration.lufs', { value: -14 });
    expect(api.put).toHaveBeenCalledWith('/settings/narration.evaluate', { value: true });
  });
});

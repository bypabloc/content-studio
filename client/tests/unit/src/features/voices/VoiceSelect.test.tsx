import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { VoiceSelect } from '@/features/voices/VoiceSelect';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const VOICES = [{ id: 'ana' }, { id: 'beto' }, { id: 'carla' }];

beforeEach(() => {
  api.get.mockImplementation(async (path: string) =>
    path === '/settings/voices.favorites'
      ? { key: 'voices.favorites', value: ['carla'] }
      : { key: path.replace('/settings/', ''), value: undefined },
  );
  api.put.mockResolvedValue({});
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

/** Los nombres de las opciones abiertas, en el orden en que se ven. */
function shownOptions(): (string | null)[] {
  return screen.queryAllByRole('option').map((option) => option.textContent);
}

function renderSelect(): void {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <VoiceSelect settingKey="select.narration.voice" label={t('narration.options.voice')} voices={VOICES} />
    </QueryClientProvider>,
  );
}

describe('VoiceSelect (spec 010, AC-9)', () => {
  it('una voz favorita aparece primero, y el resto sigue en su orden', async () => {
    renderSelect();

    await userEvent.click(await screen.findByRole('combobox', { name: t('narration.options.voice') }));

    // Las favoritas llegan con su propia consulta: se espera a que el orden quede fijo.
    await waitFor(() => expect(shownOptions()).toEqual(['carla', 'ana', 'beto']));
  });

  it('sin favoritas, las voces quedan en su orden', async () => {
    api.get.mockImplementation(async (path: string) => ({ key: path.replace('/settings/', ''), value: [] }));
    renderSelect();

    await userEvent.click(await screen.findByRole('combobox', { name: t('narration.options.voice') }));

    await waitFor(() => expect(shownOptions()).toEqual(['ana', 'beto', 'carla']));
  });
});

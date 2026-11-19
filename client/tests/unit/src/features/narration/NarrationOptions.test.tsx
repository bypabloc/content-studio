import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NarrationOptions } from '@/features/narration/NarrationOptions';
import { t } from '@/shared/i18n/t';

// La API: el catálogo de narración y los ajustes (sin ninguno guardado, salvo lo que el test cambia).
const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const CATALOG = {
  engines: [
    { id: 'voxcpm2', license: 'Apache-2.0', commercial: true, installed: true, recommended: true, note: '', batch: false },
    { id: 'omnivoice', license: 'CC-BY-NC-4.0', commercial: false, installed: true, recommended: false, note: '', batch: true },
  ],
  styles: [
    { id: 'expert', recommended: true },
    { id: 'dramatic', recommended: false },
  ],
  voices: [{ id: 'yesid', language: 'es' }],
};

beforeEach(() => {
  api.get.mockImplementation(async (path: string) =>
    path === '/catalog/narration' ? CATALOG : { key: path.replace('/settings/', ''), value: null },
  );
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({
    key: path.replace('/settings/', ''),
    value: body.value,
  }));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Espera a que llegue el catálogo: sin sus opciones, el selector del motor no tiene nada que elegir.
async function renderOptions(): Promise<HTMLSelectElement> {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <NarrationOptions />
    </QueryClientProvider>,
  );
  await screen.findByRole('option', { name: '★ voxcpm2' });
  return screen.getByRole('combobox', { name: t('narration.options.engine') }) as HTMLSelectElement;
}

describe('NarrationOptions', () => {
  it('marca con ★ la opción recomendada de cada selector', async () => {
    await renderOptions();

    expect(await screen.findByRole('option', { name: '★ voxcpm2' })).toBeTruthy();
    expect(await screen.findByRole('option', { name: '★ expert' })).toBeTruthy();
  });

  it('AC-7: elegir un motor con licencia no comercial pide aceptarla, y al cancelar vuelve a la opción anterior', async () => {
    const engine = await renderOptions();

    fireEvent.change(engine, { target: { value: 'omnivoice' } });

    expect(await screen.findByRole('dialog', { name: t('license.title', { engine: 'omnivoice' }) })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: t('license.cancel') }));
    await waitFor(() => expect(engine.value).toBe('voxcpm2'));
    expect(api.put).not.toHaveBeenCalled();
  });

  it('AC-7: al aceptar, queda guardada la licencia y no vuelve a preguntar', async () => {
    const engine = await renderOptions();

    fireEvent.change(engine, { target: { value: 'omnivoice' } });
    fireEvent.click(await screen.findByRole('button', { name: t('license.accept') }));

    await waitFor(() => expect(engine.value).toBe('omnivoice'));
    expect(api.put).toHaveBeenCalledWith('/settings/narration.license.accepted.omnivoice', { value: true });
    fireEvent.change(engine, { target: { value: 'voxcpm2' } });
    fireEvent.change(engine, { target: { value: 'omnivoice' } });
    await waitFor(() => expect(engine.value).toBe('omnivoice'));
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('«Avanzado» muestra la masterización, la semilla y los reintentos', async () => {
    await renderOptions();

    fireEvent.click(screen.getByRole('button', { name: t('narration.advanced.toggle') }));

    expect(await screen.findByRole('combobox', { name: t('narration.advanced.master') })).toBeTruthy();
    expect(screen.getByRole('spinbutton', { name: t('narration.advanced.seed') })).toBeTruthy();
    expect(screen.getByRole('spinbutton', { name: t('narration.advanced.retries') })).toBeTruthy();
  });
});

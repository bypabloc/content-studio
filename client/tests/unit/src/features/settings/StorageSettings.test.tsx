import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { StorageSettings } from '@/features/settings/StorageSettings';

const { api, open } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn() }, open: vi.fn() }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-dialog', () => ({ open }));

beforeEach(() => {
  api.get.mockResolvedValue({
    engines: 'C:/Users/test/Content Studio/engines',
    outputs: 'C:/Users/test/Documents/Content Studio',
    engines_used_bytes: 2_000_000_000,
    engines_free_bytes: 10_000_000_000,
    outputs_used_bytes: 500_000_000,
    outputs_free_bytes: 10_000_000_000,
  });
  api.post.mockResolvedValue({ id: 3, status: 'queued' });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

function renderSettings() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <StorageSettings />
    </QueryClientProvider>,
  );
}

describe('StorageSettings', () => {
  it('muestra las rutas, espacio usado y libre', async () => {
    renderSettings();

    expect(await screen.findByText('C:/Users/test/Content Studio/engines')).toBeTruthy();
    expect(screen.getByText(/2 GB/)).toBeTruthy();
    expect(screen.getAllByText(/10 GB/)).toHaveLength(2);
  });

  it('confirma y encola el traslado a una carpeta elegida', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    open.mockResolvedValueOnce('D:/Studio/engines');
    const user = userEvent.setup();
    renderSettings();

    await user.click(await screen.findByRole('button', { name: 'Cambiar carpeta de Motores' }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/storage/move', { target: 'engines', to: 'D:/Studio/engines' }));
    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('aprox. 1 min'));
  });

  it('formatea tamaños pequeños y cancela si el diálogo no devuelve una carpeta', async () => {
    api.get.mockResolvedValueOnce({
      engines: 'C:/engine', outputs: 'C:/output',
      engines_used_bytes: 500, engines_free_bytes: 900,
      outputs_used_bytes: 2_000, outputs_free_bytes: 4_000,
    });
    open.mockResolvedValueOnce(null);
    const user = userEvent.setup();
    renderSettings();

    expect(await screen.findByText('Usado: 500 B')).toBeTruthy();
    expect(screen.getByText('Usado: 2 KB')).toBeTruthy();
    await user.click(screen.getByRole('button', { name: 'Cambiar carpeta de Motores' }));
    expect(api.post).not.toHaveBeenCalled();
  });

  it('muestra una estimación en horas y respeta la cancelación de confirmación', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    api.get.mockResolvedValueOnce({
      engines: 'C:/engine', outputs: 'C:/output',
      engines_used_bytes: 400_000_000_000, engines_free_bytes: 1,
      outputs_used_bytes: 0, outputs_free_bytes: 1,
    });
    open.mockResolvedValueOnce('D:/engine');
    const user = userEvent.setup();
    renderSettings();

    await user.click(await screen.findByRole('button', { name: 'Cambiar carpeta de Motores' }));

    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('aprox. 2 h 14 min'));
    expect(api.post).not.toHaveBeenCalled();
  });

  it('muestra carga y error de la consulta sin inventar rutas', async () => {
    api.get.mockReturnValueOnce(new Promise(() => undefined));
    const loading = renderSettings();
    expect(screen.getByText('Cargando almacenamiento…')).toBeTruthy();
    loading.unmount();

    api.get.mockRejectedValueOnce(new Error('offline'));
    renderSettings();
    expect(await screen.findByText('No se pudo cargar el almacenamiento.')).toBeTruthy();
  });
});

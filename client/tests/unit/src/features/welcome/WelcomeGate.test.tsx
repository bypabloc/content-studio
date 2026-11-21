import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { WelcomeGate } from '@/features/welcome/WelcomeGate';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const storage = {
  engines: 'C:/Studio/engines', outputs: 'C:/Studio/outputs',
  engines_used_bytes: 0, engines_free_bytes: 10, outputs_used_bytes: 0, outputs_free_bytes: 10,
};
const system = { ffmpeg: null, git: null, gpu: null };

function renderGate() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <WelcomeGate />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path === '/engines') return [];
    if (path === '/system') return system;
    if (path === '/storage') return storage;
    return { key: path.split('/').pop(), value: null };
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('WelcomeGate', () => {
  it('abre la bienvenida sin motores ni preferencia y muestra el aviso de FFmpeg', async () => {
    renderGate();

    expect(await screen.findByRole('dialog', { name: 'Bienvenida a Content Studio' })).toBeTruthy();
    expect(screen.getByText('FFmpeg no está disponible en el PATH. Algunas funciones necesitan esta herramienta.')).toBeTruthy();
    const alert = screen.getByText(/FFmpeg no está disponible/).closest('[role="status"]');
    expect(alert).not.toBeNull();
    fireEvent.click(alert!.querySelector('button')!);
    expect(api.post).toHaveBeenCalledWith('/system/tools/ffmpeg/install');
  });

  it('marca la bienvenida como completada al agregar la selección a la cola', async () => {
    renderGate();

    await screen.findByRole('dialog', { name: 'Bienvenida a Content Studio' });
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    fireEvent.click(screen.getByRole('button', { name: 'Agregar a la cola e ir a Narración' }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/welcome.done', { value: true }));
  });

  it('omite la bienvenida si ya hay un motor externo', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/engines') return [{ engine: 'qwen', status: 'external' }];
      if (path === '/system') return system;
      if (path === '/storage') return storage;
      return { key: 'welcome.done', value: true };
    });
    renderGate();
    expect(await screen.findByRole('status')).toBeTruthy();
    expect(screen.queryByRole('dialog', { name: 'Bienvenida a Content Studio' })).toBeNull();
    expect(screen.getByText(/FFmpeg no está disponible/)).toBeTruthy();
  });

  it('omite la bienvenida si ya se guardó welcome.done', async () => {
    api.get.mockImplementation(async (path: string) => {
      if (path === '/engines') return [];
      if (path === '/system') return { ffmpeg: { path: 'ffmpeg.exe', version: '9.1' }, git: null, gpu: null };
      if (path === '/storage') return storage;
      return { key: 'welcome.done', value: true };
    });
    renderGate();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/storage'));
    expect(screen.queryByRole('dialog', { name: 'Bienvenida a Content Studio' })).toBeNull();
  });
});

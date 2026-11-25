import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { HfTokenField } from '@/features/engines/HfTokenField';
import { openUrl } from '@tauri-apps/plugin-opener';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), del: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('@tauri-apps/plugin-opener', () => ({ openUrl: vi.fn() }));

const TOKEN = 'hf_' + 'a'.repeat(34);

function renderField(configured: boolean) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <HfTokenField configured={configured} />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('HfTokenField (spec 034, AC-5)', () => {
  it('sin token muestra el campo, el enlace para aceptar las condiciones y Guardar deshabilitado', () => {
    renderField(false);

    expect(screen.getByLabelText('Token de Hugging Face')).toBeTruthy();
    expect((screen.getByRole('button', { name: 'Guardar token' }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole('link', { name: 'Acepta las condiciones del modelo en Hugging Face' })).toBeTruthy();
  });

  it('guardar envía el token al servidor', async () => {
    api.put.mockResolvedValue({ configured: true });
    renderField(false);

    await userEvent.type(screen.getByLabelText('Token de Hugging Face'), TOKEN);
    await userEvent.click(screen.getByRole('button', { name: 'Guardar token' }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/credentials/huggingface', { token: TOKEN }));
  });

  it('con token guardado dice Token guardado y Quitar borra el token', async () => {
    api.del.mockResolvedValue({ configured: false });
    renderField(true);

    expect(screen.getByText('Token guardado')).toBeTruthy();
    await userEvent.click(screen.getByRole('button', { name: 'Quitar' }));

    await waitFor(() => expect(api.del).toHaveBeenCalledWith('/credentials/huggingface'));
  });

  it('el enlace abre el modelo en el navegador, no dentro de la app', async () => {
    renderField(false);

    await userEvent.click(screen.getByRole('link', { name: 'Acepta las condiciones del modelo en Hugging Face' }));

    expect(openUrl).toHaveBeenCalledWith('https://huggingface.co/pyannote/speaker-diarization-community-1');
  });
});

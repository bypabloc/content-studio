import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useRecordingLog } from '@/features/recording/recordingLog';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn() },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

afterEach(() => {
  vi.clearAllMocks();
});

// El ajuste llega por la API: con el valor guardado, la función de registro ya sabe si escribe.
async function logWithSetting(saved: unknown) {
  api.get.mockResolvedValue({ key: 'diagnostics.recording_log', value: saved });
  api.post.mockResolvedValue(undefined);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => createElement(QueryClientProvider, { client }, children);
  const { result } = renderHook(() => useRecordingLog(), { wrapper });
  // Esperamos a que la caché tenga el ajuste y a que el hook lo vea: un plazo fijo fallaba con la CPU cargada.
  await waitFor(() => expect(client.getQueryState(['settings', 'diagnostics.recording_log'])?.status).toBe('success'));
  await act(async () => {});
  return result.current;
}

describe('useRecordingLog (spec 010, D-7)', () => {
  it('con el ajuste apagado por defecto no escribe nada ni llama a la API', async () => {
    const log = await logWithSetting(undefined);

    log('record.start', { device: 'mic-1' });

    expect(api.post).not.toHaveBeenCalled();
  });

  it('con el ajuste encendido manda el evento con su detalle', async () => {
    const log = await logWithSetting(true);

    log('record.start', { device: 'mic-1' });

    expect(api.post).toHaveBeenCalledWith('/diagnostics/recording', { event: 'record.start', detail: { device: 'mic-1' } });
  });

  it('un fallo al anotar no llega a quien grabó', async () => {
    const log = await logWithSetting(true);
    api.post.mockRejectedValueOnce(new Error('disco lleno'));

    log('room.failed');
    // El rechazo se procesa en el siguiente turno: si no hubiera `catch`, la prueba fallaría por rechazo sin manejar.
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(api.post).toHaveBeenCalledTimes(1);
  });
});

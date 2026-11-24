import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { defaultRect, ReframePreview } from '@/features/convert/ReframePreview';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: vi.fn(), queryUrl: (path: string) => `http://test${path}` },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const source = { path: '/media/charla.mp4', width: 1920, height: 1080 };
const target = { width: 1080, height: 1920 };

function renderPreview(onChange = vi.fn()) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <ReframePreview source={source} target={target} onChange={onChange} />
    </QueryClientProvider>,
  );
  return onChange;
}

beforeEach(() => {
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/settings/')) return { key: path, value: null };
    throw new Error(`GET inesperado: ${path}`);
  });
  // Como el server: el PUT devuelve el ajuste guardado, y `useSetting` lo deja en la caché.
  api.put.mockImplementation(async (path: string, body: { value: unknown }) => ({ key: path.replace('/settings/', ''), value: body.value }));
  // La zona del cuadro mide 400 x 300 px en la prueba: el arrastre se mide en fracciones de ese tamaño.
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
    left: 0,
    top: 0,
    right: 400,
    bottom: 300,
    width: 400,
    height: 300,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  } as DOMRect);
});

afterEach(() => {
  vi.restoreAllMocks();
  cleanup();
  api.get.mockReset();
  api.post.mockReset();
});

describe('ReframePreview', () => {
  it('AC-11: con manual, arrastrar el rectángulo deja sus coordenadas normalizadas en el encuadre', async () => {
    const onChange = renderPreview();

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.reframe.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('convert.reframe.manual') }));

    const area = await screen.findByRole('group', { name: t('convert.reframe.area') });
    const rect = screen.getByTestId('crop-rect');
    fireEvent.pointerDown(rect, { clientX: 100, clientY: 100, pointerId: 1 });
    fireEvent.pointerMove(area, { clientX: 140, clientY: 100, pointerId: 1 });
    fireEvent.pointerUp(area, { clientX: 140, clientY: 100, pointerId: 1 });

    await waitFor(() => {
      const reframe = onChange.mock.lastCall?.[0];
      expect(reframe.mode).toBe('manual');
      // El cuadro 9:16 de un 16:9 mide 0,3164 del ancho; arrancó centrado (x 0,3418) y se movió 40 de 400 px.
      expect(reframe.x).toBeCloseTo(0.4418, 3);
      expect(reframe.w).toBeCloseTo(0.3164, 3);
      expect(reframe.y).toBe(0);
      expect(reframe.h).toBe(1);
    });
  });

  it('con el encuadre centrado no hace falta ninguna elección más', async () => {
    const onChange = renderPreview();

    await waitFor(() => expect(onChange.mock.lastCall?.[0]).toEqual({ mode: 'center' }));
  });

  it('follow-face no tiene encuadre hasta que se analiza la cara', async () => {
    const onChange = renderPreview();

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.reframe.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('convert.reframe.follow-face') }));

    expect(await screen.findByRole('button', { name: t('convert.reframe.analyze') })).toBeTruthy();
    await waitFor(() => expect(onChange.mock.lastCall?.[0]).toBeNull());
  });

  it('un video vertical en un destino horizontal se encuadra centrado en alto', () => {
    const rect = defaultRect({ width: 1080, height: 1920 }, { width: 1920, height: 1080 });

    expect(rect.x).toBe(0);
    expect(rect.w).toBe(1);
    expect(rect.h).toBeCloseTo(0.3164, 4);
    expect(rect.y).toBeCloseTo(0.3418, 4);
  });

  it('con barras o desenfoque, el encuadre es fijo y se reporta al elegirlo', async () => {
    const onChange = renderPreview();

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.reframe.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('convert.reframe.fit-bars') }));
    await waitFor(() => expect(onChange.mock.lastCall?.[0]).toEqual({ mode: 'fit-bars', color: 'black' }));

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.reframe.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('convert.reframe.fit-blur') }));
    await waitFor(() => expect(onChange.mock.lastCall?.[0]).toEqual({ mode: 'fit-blur', strength: 20 }));
  });

  it('seguir a la persona analiza las caras y, al terminar, pasa la trayectoria', async () => {
    let polls = 0;
    api.get.mockImplementation(async (path: string) => {
      if (path.startsWith('/settings/')) return { key: path, value: null };
      if (path === '/jobs/5') {
        polls += 1;
        const running = polls === 1;
        return { id: 5, kind: 'media.reframe_track', status: running ? 'running' : 'done', progress: running ? 0.5 : 1, output_dir: 'out/reframe/5' };
      }
      throw new Error(`GET inesperado: ${path}`);
    });
    api.post.mockResolvedValue({ id: 5, kind: 'media.reframe_track', status: 'queued', progress: 0, output_dir: null });
    const onChange = renderPreview();

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.reframe.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('convert.reframe.follow-face') }));
    await userEvent.click(await screen.findByRole('button', { name: t('convert.reframe.analyze') }));

    expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'media.reframe_track', params: { input: '/media/charla.mp4' } });
    expect(await screen.findByText(t('convert.reframe.analyzing', { percent: 50 }))).toBeTruthy();
    await waitFor(() => expect(onChange.mock.lastCall?.[0]).toEqual({ mode: 'follow-face', track: 'out/reframe/5/track.json' }), {
      timeout: 3000,
    });
  });
});

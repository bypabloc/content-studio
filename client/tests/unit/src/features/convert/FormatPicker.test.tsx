import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { Catalog } from '@/features/convert/convertOptions';
import { type FormatChoice, FormatPicker } from '@/features/convert/FormatPicker';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: vi.fn(), queryUrl: vi.fn() },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const catalog: Catalog = {
  formats: [
    { id: 'mp3', kind: 'audio' },
    { id: 'wav', kind: 'audio' },
    { id: 'mp4-h264', kind: 'video' },
    { id: 'gif', kind: 'gif' },
  ],
  presets: [
    { id: 'reels', width: 1080, height: 1920, fps: 30, reframe: 'center', recommended: true },
    { id: 'youtube-1080', width: 1920, height: 1080, fps: 30, reframe: 'center', recommended: false },
  ],
};

function renderPicker(kind: 'audio' | 'video', onChange = vi.fn()) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <FormatPicker kind={kind} catalog={catalog} onChange={onChange} />
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
});

afterEach(() => {
  cleanup();
  api.get.mockReset();
  api.put.mockReset();
});

describe('FormatPicker', () => {
  it('con audio, el formato ★ es MP3 y la calidad ★ es V2', async () => {
    renderPicker('audio');

    const format = (await screen.findByRole('combobox', { name: t('convert.format.label') })) as HTMLInputElement;
    expect(format.value).toContain('★');
    expect(format.value).toContain(t('convert.format.mp3'));
  });

  it('con video, el formato ★ es MP4 (H.264)', async () => {
    renderPicker('video');

    expect(((await screen.findByRole('combobox', { name: t('convert.format.label') })) as HTMLInputElement).value).toContain(
      t('convert.format.mp4-h264'),
    );
  });

  it('elegir Redes muestra el preset ★ según la proporción y lo reporta con la elección', async () => {
    const onChange = renderPicker('video');

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.format.label') }));
    await userEvent.click(await screen.findByRole('option', { name: new RegExp(t('convert.format.social')) }));

    const preset = (await screen.findByRole('combobox', { name: t('convert.social.preset') })) as HTMLInputElement;
    expect(preset.value).toContain(t('convert.preset.reels'));
    await waitFor(() => {
      const choice: FormatChoice = onChange.mock.lastCall?.[0];
      expect(choice).toMatchObject({ format: 'social', preset: 'reels' });
    });
  });

  it('recuerda la última elección de formato en settings', async () => {
    renderPicker('audio');

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.format.label') }));
    await userEvent.click(await screen.findByRole('option', { name: new RegExp(t('convert.format.wav')) }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/settings/select.convert.format', { value: 'wav' }));
  });

  it('con video, Avanzado abre la resolución', async () => {
    renderPicker('video');

    await userEvent.click(await screen.findByRole('button', { name: t('convert.advanced.label') }));

    expect(await screen.findByRole('combobox', { name: t('convert.advanced.resolution') })).toBeTruthy();
  });

  it('el GIF no tiene Avanzado', async () => {
    renderPicker('video');

    await userEvent.click(await screen.findByRole('combobox', { name: t('convert.format.label') }));
    await userEvent.click(await screen.findByRole('option', { name: new RegExp(t('convert.format.gif')) }));

    await waitFor(() => expect(screen.queryByRole('button', { name: t('convert.advanced.label') })).toBeNull());
  });
});

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MixEditor } from '@/features/mix/MixEditor';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({
  api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: (path: string) => `file://${path}` },
}));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));

const PARAMS = {
  mode: 'transcript',
  duck_db: -12,
  ramp_ms: 300,
  music_db: -6,
  voice_db: 0,
  intro: 0,
  outro: 0,
  lufs: -14,
  merge_gap: 0.6,
  pre: 0.2,
  post: 0.4,
};

let status = 'ready';
let renderJobs: unknown[] = [];

function project(state: string) {
  return {
    id: 7,
    name: 'charla',
    voice: 'voz.wav',
    music: 'musica.wav',
    video: null,
    video_mode: 'replace',
    regions: [[1, 2]],
    params: PARAMS,
    transcribe_job: 3,
    status: state,
  };
}

function renderEditor() {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MixEditor projectId={7} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  status = 'ready';
  renderJobs = [];
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/jobs')) return renderJobs;
    return path.endsWith('/curve') ? { total: 10, points: [] } : project(status);
  });
  api.post.mockResolvedValue({ id: 9 });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('MixEditor (spec 016, D-4)', () => {
  it('espera mientras la voz se transcribe', async () => {
    status = 'transcribing';
    renderEditor();

    expect(await screen.findByText(t('mix.status.transcribing'))).toBeTruthy();
  });

  it('avisa si la transcripción de la voz falló', async () => {
    status = 'failed';
    renderEditor();

    expect(await screen.findByText(t('mix.status.failed'))).toBeTruthy();
  });

  it('con el proyecto listo, manda la mezcla a la cola', async () => {
    renderEditor();

    await userEvent.click(await screen.findByRole('button', { name: t('mix.render') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'mix.render', params: { mix_id: 7 } }),
    );
  });

  it('mover una región guarda sus tramos nuevos', async () => {
    renderEditor();

    fireEvent.keyDown(await screen.findByRole('button', { name: t('mix.region.label', { n: 1 }) }), {
      key: 'ArrowRight',
    });

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/mix/7', { regions: [[1.1, 2.1]], params: {} }));
  });

  it('cambiar el modo de ducking guarda ese parámetro', async () => {
    renderEditor();

    await userEvent.click(await screen.findByRole('combobox', { name: t('mix.mode.label') }));
    await userEvent.click(await screen.findByRole('option', { name: t('mix.mode.sidechain') }));

    await waitFor(() =>
      expect(api.put).toHaveBeenCalledWith('/mix/7', { regions: [[1, 2]], params: { mode: 'sidechain' } }),
    );
  });

  it('la vista previa suena y se para desde su botón', async () => {
    const source = { buffer: null, connect: vi.fn(), start: vi.fn(), stop: vi.fn() };
    const context = {
      currentTime: 0,
      destination: {},
      createGain: () => ({ gain: { cancelScheduledValues: vi.fn(), linearRampToValueAtTime: vi.fn() }, connect: vi.fn() }),
      createBufferSource: () => source,
      decodeAudioData: vi.fn(async () => ({})),
      close: vi.fn(async () => undefined),
    };
    vi.stubGlobal('AudioContext', function AudioContextStub() {
      return context;
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ arrayBuffer: async () => new ArrayBuffer(4) })),
    );
    renderEditor();

    await userEvent.click(await screen.findByRole('button', { name: t('mix.preview.play') }));
    await userEvent.click(await screen.findByRole('button', { name: t('mix.preview.stop') }));

    expect(context.close).toHaveBeenCalled();
    expect(await screen.findByRole('button', { name: t('mix.preview.play') })).toBeTruthy();
    vi.unstubAllGlobals();
  });

  it('si el render falló por música corta, lo dice con su código (AC-4)', async () => {
    renderJobs = [{ id: 9, status: 'failed', error_code: 'music_too_short', params: { mix_id: 7 } }];
    renderEditor();

    expect(await screen.findByRole('alert', {}, { timeout: 4000 })).toBeTruthy();
    expect(screen.getByText(t('error.music_too_short'))).toBeTruthy();
  });

  it.each([
    ['mix.duck.label', '-9', { duck_db: -9 }],
    ['mix.ramp.label', '600', { ramp_ms: 600 }],
    ['mix.music.label', '-3', { music_db: -3 }],
    ['mix.intro.label', '2', { intro: 2 }],
    ['mix.outro.label', '3', { outro: 3 }],
    ['mix.lufs.label', '-16', { lufs: -16 }],
  ] as const)('cambiar «%s» guarda ese parámetro', async (label, option, change) => {
    renderEditor();

    await userEvent.click(await screen.findByRole('combobox', { name: t(label) }));
    await userEvent.click(await screen.findByRole('option', { name: option }));

    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/mix/7', { regions: [[1, 2]], params: change }));
  });

  it('si la cola rechaza la mezcla, se queda en el editor', async () => {
    api.post.mockRejectedValueOnce(new Error('sin espacio'));
    renderEditor();

    await userEvent.click(await screen.findByRole('button', { name: t('mix.render') }));

    await waitFor(() => expect(api.post).toHaveBeenCalled());
    expect(screen.getByRole('button', { name: t('mix.render') })).toBeTruthy();
  });
});

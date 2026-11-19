import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import WaveSurfer from 'wavesurfer.js';
import { NarrationResult } from '@/features/narration/NarrationResult';
import type { components } from '@/shared/api/schema';
import { t } from '@/shared/i18n/t';

type Job = components['schemas']['Job'];

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
vi.mock('wavesurfer.js', () => ({
  default: { create: vi.fn(() => ({ on: vi.fn(), playPause: vi.fn(), destroy: vi.fn() })) },
}));

const DIR = 'D:/out/narration/2026-11-19-7-hola';
const JOB = { id: 7, kind: 'narration', status: 'done', output_dir: DIR, params: { model: 'voxcpm2' } } as unknown as Job;
const SCRIPT = { wav: 'voxcpm2-expert.wav', segments: [{ text: 'Hola.' }, { text: 'Adiós.' }] };
// Lo que escribe `save_metadata`: la evaluación de whisper por párrafo, con los textos como los dijo el motor.
const EVALUATED = {
  evaluation: {
    rounds: 1,
    ok: false,
    observations: [
      'paragraph 2: change "adiós" -> "a dios"',
      'paragraph 1: 0.8 s of silence inside the paragraph',
      'notice, paragraph 2: rhythm 4.0 words/s (median 3.0)',
      'the take was cut short',
    ],
  },
};
const NOT_EVALUATED = { evaluation: null };
const INFO = { duration: 2.5, lufs: -16.2, true_peak: -1.4 };
const PEAKS = { peaks: [0.1, 0.9] };

let take: unknown = EVALUATED;

beforeEach(() => {
  take = EVALUATED;
  api.fileUrl.mockImplementation((path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}&token=t`);
  api.get.mockImplementation(async (path: string) => {
    if (path.includes('script.json')) return SCRIPT;
    if (path.includes('.json')) return take;
    if (path.startsWith('/media/info')) return INFO;
    return PEAKS;
  });
  api.post.mockResolvedValue({ id: 8 });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderResult(job: Job = JOB) {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <NarrationResult job={job} />
    </QueryClientProvider>,
  );
}

describe('NarrationResult', () => {
  it('muestra la toma con su forma de onda, su LUFS y su pico real', async () => {
    renderResult();

    expect(
      await screen.findByText(t('narration.result.loudness', { lufs: '-16.2', peak: '-1.4' })),
    ).toBeTruthy();
    await waitFor(() =>
      expect(WaveSurfer.create).toHaveBeenCalledWith(
        expect.objectContaining({ url: expect.stringContaining('voxcpm2-expert.wav'), peaks: [[0.1, 0.9]] }),
      ),
    );
  });

  it('resalta, párrafo a párrafo, lo que whisper oyó distinto y los silencios y ritmos avisados', async () => {
    renderResult();

    // El párrafo llega con el guion; la evaluación, con su propio .json: se espera a que se pinte.
    const paragraph = (await screen.findByText('Adiós.')).closest('li') as HTMLElement;
    expect(await within(paragraph).findByText('adiós', { selector: 'del' })).toBeTruthy();
    expect(within(paragraph).getByText('a dios', { selector: 'ins' })).toBeTruthy();
    expect(screen.getByText(t('narration.result.silence', { seconds: '0.8' }))).toBeTruthy();
    expect(screen.getByText(t('narration.result.rhythm', { speed: '4.0', median: '3.0' }))).toBeTruthy();
    // Lo que no es de un párrafo va aparte, tal como lo dijo el motor.
    expect(screen.getByText(t('narration.result.other'))).toBeTruthy();
    expect(screen.getByText('the take was cut short')).toBeTruthy();
  });

  it('Regenerar encola narration.regenerate con el trabajo y el índice del párrafo (desde 0)', async () => {
    renderResult();
    await screen.findByText('Adiós.');

    fireEvent.click(screen.getAllByRole('button', { name: t('narration.result.regenerate') })[1]);

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/jobs', { kind: 'narration.regenerate', params: { source_job: 7, index: 1 } }),
    );
  });

  it('una toma sin evaluar lo dice y no marca diferencias', async () => {
    take = NOT_EVALUATED;
    renderResult();

    expect(await screen.findByText(t('narration.result.unevaluated'))).toBeTruthy();
    expect(document.querySelector('del')).toBeNull();
  });

  it('un trabajo sin carpeta de salida no pide nada', () => {
    renderResult({ ...JOB, output_dir: null } as Job);

    expect(api.get).not.toHaveBeenCalled();
  });
});

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
// Las tomas de un mismo texto tienen su propio test (CompareTakes): aquí solo importa que el botón las abre.
vi.mock('@/features/narration/CompareTakes', async () => {
  const { createElement } = await import('react');
  return { CompareTakes: ({ groupKey }: { groupKey: string }) => createElement('p', null, `tomas de ${groupKey}`) };
});

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
  window.location.hash = '';
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
  it('abre en el Editor con la ruta de la toma', async () => {
    renderResult();
    await screen.findByText('Adiós.');

    fireEvent.click(await screen.findByRole('button', { name: 'Abrir en Editor' }));

    expect(new URLSearchParams(window.location.hash.split('?')[1]).getAll('add')).toEqual([
      `${DIR}/voxcpm2-expert.wav`,
    ]);
  });

  it('manda la toma a Mezcla con el parámetro común path', async () => {
    renderResult();
    await screen.findByText('Adiós.');

    fireEvent.click(screen.getByRole('button', { name: t('mix.send') }));

    expect(window.location.hash).toBe(`#/mix?path=${encodeURIComponent(`${DIR}/voxcpm2-expert.wav`)}`);
  });

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
    const paragraph = (await screen.findByText('Adiós.')).closest('[role="listitem"]') as HTMLElement;
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

    fireEvent.click(screen.getAllByRole('button', { name: t('action.regenerate') })[1]);

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

  it('Comparar abre las tomas del mismo texto, si el trabajo tiene grupo', async () => {
    renderResult({ ...JOB, group_key: 'narration:abc' } as Job);
    await screen.findByText('Adiós.');

    fireEvent.click(screen.getByRole('button', { name: t('action.compare') }));

    expect(await screen.findByText('tomas de narration:abc')).toBeTruthy();
  });

  it('Comparar y Regenerar son solo íconos con su nombre (spec 009, D-4)', async () => {
    renderResult({ ...JOB, group_key: 'narration:abc' } as Job);
    await screen.findByText('Adiós.');

    const compare = screen.getByRole('button', { name: t('action.compare') });
    expect(compare.textContent).toBe('');
    expect(compare.querySelector('svg.lucide-arrow-left-right')).not.toBeNull();
    const regenerate = screen.getAllByRole('button', { name: t('action.regenerate') })[0];
    expect(regenerate.textContent).toBe('');
    expect(regenerate.querySelector('svg.lucide-refresh-cw')).not.toBeNull();
  });

  it('Subtitular encola subtitles.create con el guion de la toma (spec 014, D-4)', async () => {
    renderResult();
    await screen.findByText('Adiós.');

    fireEvent.click(screen.getByRole('button', { name: t('narration.result.subtitle') }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/jobs',
        expect.objectContaining({
          kind: 'subtitles.create',
          params: expect.objectContaining({ origin: 'narration', script: 'Hola. Adiós.', language: 'es' }),
        }),
      ),
    );
  });

  it('un trabajo sin carpeta de salida no pide nada', () => {
    renderResult({ ...JOB, output_dir: null } as Job);

    expect(api.get).not.toHaveBeenCalled();
  });
});

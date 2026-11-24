import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import WaveSurfer from 'wavesurfer.js';
import { CompareTakes } from '@/features/narration/CompareTakes';
import { t } from '@/shared/i18n/t';

const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), put: vi.fn(), post: vi.fn(), del: vi.fn(), fileUrl: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => api }));
const { makeWave } = vi.hoisted(() => {
  function createWave() {
    const handlers = new Map<string, () => void>();
    return {
      on: vi.fn((event: string, handler: () => void) => {
        handlers.set(event, handler);
      }),
      emit: (event: string) => handlers.get(event)?.(),
      playPause: vi.fn(() => Promise.resolve()),
      pause: vi.fn(),
      destroy: vi.fn(),
    };
  }
  return { makeWave: createWave };
});
vi.mock('wavesurfer.js', () => ({ default: { create: vi.fn(() => makeWave()) } }));

// Dos tomas del mismo texto (AC-10): una de la narración y otra de su regeneración.
function job(id: number, kind: string, status: string, model: string, starred = false) {
  return {
    id,
    kind,
    status,
    starred,
    group_key: 'narration:abc',
    output_dir: `D:/out/${id}`,
    params: { model, style: 'expert', voice: 'yesid' },
  };
}
let jobs = [
  job(3, 'narration', 'done', 'voxcpm2'),
  job(4, 'narration.regenerate', 'done', 'omnivoice'),
  job(5, 'narration', 'queued', 'voxcpm2'),
];
const SCRIPT = { wav: 'voxcpm2-expert.wav', segments: [{ text: 'Hola.' }] };
const TAKE = { seed: 42, duration_s: 2.5, evaluation: { rounds: 1, ok: true, observations: [] } };
const INFO = { duration: 2.5, lufs: -16.2, true_peak: -1.4 };

beforeEach(() => {
  jobs = [
    job(3, 'narration', 'done', 'voxcpm2'),
    job(4, 'narration.regenerate', 'done', 'omnivoice'),
    job(5, 'narration', 'queued', 'voxcpm2'),
  ];
  api.fileUrl.mockImplementation((path: string) => `http://127.0.0.1:9000/files?path=${encodeURIComponent(path)}`);
  api.get.mockImplementation(async (path: string) => {
    if (path.startsWith('/jobs?group_key=')) return jobs;
    if (path.includes('script.json')) return SCRIPT;
    if (path.includes('.json')) return TAKE;
    if (path.startsWith('/media/info')) return INFO;
    return { peaks: [0.1, 0.9] };
  });
  api.post.mockImplementation(async (path: string) => {
    const id = Number(/^\/jobs\/(\d+)\/star$/.exec(path)?.[1]);
    jobs = jobs.map((item) => ({ ...item, starred: item.id === id }));
    return jobs.find((item) => item.id === id);
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderCompare() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <CompareTakes groupKey="narration:abc" />
    </QueryClientProvider>,
  );
}

describe('CompareTakes', () => {
  it('muestra cada toma terminada del texto en su columna, con su motor y su estilo; las que esperan no salen', async () => {
    renderCompare();

    const columns = await screen.findAllByRole('article');
    expect(columns).toHaveLength(2);
    expect(within(columns[0]).getByText('voxcpm2')).toBeTruthy();
    expect(within(columns[1]).getByText('omnivoice')).toBeTruthy();
    expect(api.get).toHaveBeenCalledWith('/jobs?group_key=narration%3Aabc');
  });

  it('Elegir marca la toma con ★ y quita la marca de la que estaba', async () => {
    renderCompare();
    const columns = await screen.findAllByRole('article');

    fireEvent.click(within(columns[1]).getByRole('button', { name: t('action.choose') }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/jobs/4/star'));
    await waitFor(() =>
      expect(within(screen.getAllByRole('article')[1]).getByText(t('narration.compare.chosen'))).toBeTruthy(),
    );
    expect(within(screen.getAllByRole('article')[0]).getByRole('button', { name: t('action.choose') })).toBeTruthy();
  });

  it('Elegir es solo una estrella con su nombre (spec 009, D-4)', async () => {
    renderCompare();
    const columns = await screen.findAllByRole('article');

    const choose = within(columns[1]).getByRole('button', { name: t('action.choose') });
    expect(choose.textContent).toBe('');
    expect(choose.querySelector('svg.lucide-star')).not.toBeNull();
  });

  it('al reproducir una toma se pausan las demás (AC-10)', async () => {
    renderCompare();
    await screen.findAllByRole('article');
    await waitFor(() => expect(WaveSurfer.create).toHaveBeenCalledTimes(2));
    const [first, second] = vi.mocked(WaveSurfer.create).mock.results.map((result) => result.value);

    (first as ReturnType<typeof makeWave>).emit('play');

    expect((second as ReturnType<typeof makeWave>).pause).toHaveBeenCalledTimes(1);
  });
});

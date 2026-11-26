import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SubtitleLane } from '@/features/editor/timeline/SubtitleLane';

const mocks = vi.hoisted(() => ({ api: { get: vi.fn() } }));
vi.mock('@/shared/api/context', () => ({ useApi: () => mocks.api }));

const project = {
  cues: [
    { id: 1, start: 0, end: 2, text: 'hola a todos', speaker: 'SPEAKER_00' },
    { id: 2, start: 2.5, end: 4, text: 'buenas tardes', speaker: 'SPEAKER_01' },
    { id: 3, start: 4, end: 5, text: 'sin hablante', speaker: null },
  ],
  speakers: {
    SPEAKER_00: { name: 'Ana', color: '#2563eb' },
    SPEAKER_01: { name: 'Luis', color: '#dc2626' },
  },
};

function renderLane(zoom: number) {
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <SubtitleLane projectId="7" zoom={zoom} />
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('SubtitleLane', () => {
  it('dibuja un bloque por cue, con la posición y el ancho de la escala de la línea de tiempo (AC-7)', async () => {
    mocks.api.get.mockResolvedValue(project);
    renderLane(80);

    const first = await screen.findByRole('group', { name: 'hola a todos' });
    expect(mocks.api.get).toHaveBeenCalledWith('/subtitles/7');
    expect(first.style.left).toBe('0px');
    expect(first.style.width).toBe('160px');
    const second = screen.getByRole('group', { name: 'buenas tardes' });
    expect(second.style.left).toBe('200px');
    expect(second.style.width).toBe('120px');
  });

  it('pinta cada bloque con el color de su hablante y muestra su nombre (AC-7)', async () => {
    mocks.api.get.mockResolvedValue(project);
    renderLane(80);

    expect((await screen.findByRole('group', { name: 'hola a todos' })).style.backgroundColor).toBe('rgb(37, 99, 235)');
    expect(screen.getByRole('group', { name: 'buenas tardes' }).style.backgroundColor).toBe('rgb(220, 38, 38)');
    expect(screen.getByText('Ana')).toBeTruthy();
  });

  it('deja neutro el bloque de un cue sin hablante', async () => {
    mocks.api.get.mockResolvedValue(project);
    renderLane(80);

    const neutral = await screen.findByRole('group', { name: 'sin hablante' });
    expect(neutral.style.backgroundColor).toBe('');
    expect(neutral.className).toContain('bg-muted');
  });
});

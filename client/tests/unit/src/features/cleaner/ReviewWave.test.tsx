import { cleanup, render } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ReviewWave } from '@/features/cleaner/ReviewWave';
import type { Cut } from '@/features/cleaner/cuts';
import WaveSurfer from 'wavesurfer.js';

// Los plugins y la onda se simulan: jsdom no dibuja la forma de onda. Se prueba la conexión con las regiones.
const { regions, instance } = vi.hoisted(() => {
  const listeners: Record<string, Array<(...args: unknown[]) => void>> = {};
  return {
    regions: {
      listeners,
      addRegion: vi.fn((options: { id: string; start: number; end: number }) => ({ ...options })),
      clearRegions: vi.fn(),
      on: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
        (listeners[event] ??= []).push(handler);
        return () => undefined;
      }),
    },
    instance: { destroy: vi.fn(), on: vi.fn(() => () => undefined) },
  };
});

vi.mock('wavesurfer.js', () => ({ default: { create: vi.fn(() => instance) } }));
vi.mock('wavesurfer.js/dist/plugins/regions.js', () => ({ default: { create: vi.fn(() => regions) } }));
vi.mock('wavesurfer.js/dist/plugins/timeline.js', () => ({ default: { create: vi.fn(() => ({})) } }));
vi.mock('wavesurfer.js/dist/plugins/zoom.js', () => ({ default: { create: vi.fn(() => ({})) } }));

function fire(event: string, region: { id: string; start?: number; end?: number }) {
  for (const handler of regions.listeners[event] ?? []) handler(region);
}

const cuts: Cut[] = [
  { start: 1, end: 2, enabled: true },
  { start: 5, end: 6, enabled: true },
];

describe('ReviewWave (spec 013, D-6)', () => {
  beforeEach(() => {
    for (const key of Object.keys(regions.listeners)) delete regions.listeners[key];
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('crea la onda sobre el medio con sus picos y una región arrastrable por corte', () => {
    const media = document.createElement('audio');
    const peaks = [0.1, 0.5];
    render(<ReviewWave media={media} peaks={peaks} duration={10} cuts={cuts} selected={0} onCutsChange={vi.fn()} onSelect={vi.fn()} />);

    expect(WaveSurfer.create).toHaveBeenCalledWith(expect.objectContaining({ media, peaks: [peaks] }));
    expect(regions.addRegion).toHaveBeenCalledWith(expect.objectContaining({ id: '0', start: 1, end: 2, drag: true, resize: true }));
    expect(regions.addRegion).toHaveBeenCalledWith(expect.objectContaining({ id: '1', start: 5, end: 6, drag: true, resize: true }));
  });

  it('arrastrar un borde edita ese corte y lo marca como editado', () => {
    const onCutsChange = vi.fn();
    render(<ReviewWave media={null} peaks={[]} duration={10} cuts={cuts} selected={0} onCutsChange={onCutsChange} onSelect={vi.fn()} />);

    fire('region-updated', { id: '1', start: 5.2, end: 6.1 });

    expect(onCutsChange).toHaveBeenCalledWith([
      { start: 1, end: 2, enabled: true },
      { start: 5.2, end: 6.1, enabled: true, edited: true },
    ]);
  });

  it('un clic en una región la selecciona y activa o desactiva', () => {
    const onCutsChange = vi.fn();
    const onSelect = vi.fn();
    render(<ReviewWave media={null} peaks={[]} duration={10} cuts={cuts} selected={0} onCutsChange={onCutsChange} onSelect={onSelect} />);

    fire('region-clicked', { id: '0' });

    expect(onSelect).toHaveBeenCalledWith(0);
    expect(onCutsChange).toHaveBeenCalledWith([
      { start: 1, end: 2, enabled: false, edited: true },
      { start: 5, end: 6, enabled: true },
    ]);
  });

  it('al desmontar destruye la onda', () => {
    const { unmount } = render(
      <ReviewWave media={null} peaks={[]} duration={10} cuts={cuts} selected={0} onCutsChange={vi.fn()} onSelect={vi.fn()} />,
    );

    unmount();

    expect(instance.destroy).toHaveBeenCalledOnce();
  });

  it('al cambiar los cortes redibuja las regiones; un corte desactivado sale en gris', () => {
    // Los picos llegan de react-query con identidad estable: una lista nueva en cada render recrearía la onda.
    const peaks: number[] = [];
    const { rerender } = render(
      <ReviewWave media={null} peaks={peaks} duration={10} cuts={cuts} selected={0} onCutsChange={vi.fn()} onSelect={vi.fn()} />,
    );
    vi.clearAllMocks();

    rerender(
      <ReviewWave
        media={null}
        peaks={peaks}
        duration={10}
        cuts={[
          { start: 1, end: 2, enabled: false },
          { start: 5, end: 6, enabled: true },
        ]}
        selected={0}
        onCutsChange={vi.fn()}
        onSelect={vi.fn()}
      />,
    );

    expect(regions.clearRegions).toHaveBeenCalledOnce();
    expect(regions.addRegion).toHaveBeenCalledWith(expect.objectContaining({ id: '0', color: 'rgba(120, 120, 120, 0.25)' }));
  });
});

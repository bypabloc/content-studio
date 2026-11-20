import { cleanup, render } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SpanPicker } from '@/features/recording/SpanPicker';

// wavesurfer necesita canvas y audio: aquí se simula, y se prueba lo que el componente le pide.
const h = vi.hoisted(() => {
  const region = { start: 0, end: 0, setOptions: vi.fn() };
  region.setOptions.mockImplementation((options: { start: number; end: number }) => {
    region.start = options.start;
    region.end = options.end;
  });
  const handlers: Record<string, (updated: unknown) => void> = {};
  const regions = {
    addRegion: vi.fn((options: { start: number; end: number }) => {
      region.start = options.start;
      region.end = options.end;
      return region;
    }),
    on: vi.fn((event: string, handler: (updated: unknown) => void) => {
      handlers[event] = handler;
    }),
  };
  const wave = { destroy: vi.fn() };
  return { handlers, region, regions, wave, create: vi.fn(() => wave) };
});

vi.mock('wavesurfer.js', () => ({ default: { create: h.create } }));
vi.mock('wavesurfer.js/dist/plugins/regions.js', () => ({ default: { create: () => h.regions } }));

beforeEach(() => {
  h.region.start = 0;
  h.region.end = 0;
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('SpanPicker (spec 010, D-4)', () => {
  it('draws the waveform from the peaks and the duration, with the region on the span', () => {
    render(<SpanPicker peaks={[0.1, 0.5]} duration={20} start={0} end={10} onChange={vi.fn()} />);

    expect(h.create).toHaveBeenCalledWith(expect.objectContaining({ peaks: [[0.1, 0.5]], duration: 20 }));
    expect(h.regions.addRegion).toHaveBeenCalledWith(expect.objectContaining({ start: 0, end: 10, drag: true, resize: true }));
  });

  it('a region dragged past 12 seconds is clamped, moved and reported', () => {
    const onChange = vi.fn();
    render(<SpanPicker peaks={[0.5]} duration={60} start={0} end={10} onChange={onChange} />);

    h.region.start = 1;
    h.region.end = 30;
    h.handlers['region-updated'](h.region);

    expect(h.region.setOptions).toHaveBeenCalledWith({ start: 1, end: 13 });
    expect(onChange).toHaveBeenCalledWith(1, 13);
  });

  it('a region already between 8 and 12 seconds is reported as it is, without moving it', () => {
    const onChange = vi.fn();
    render(<SpanPicker peaks={[0.5]} duration={60} start={0} end={10} onChange={onChange} />);

    h.region.start = 2;
    h.region.end = 12;
    h.handlers['region-updated'](h.region);

    expect(h.region.setOptions).not.toHaveBeenCalled();
    expect(onChange).toHaveBeenCalledWith(2, 12);
  });

  it('changing the fields moves the region (the waveform stays while the same file is open)', () => {
    const peaks = [0.5];
    const { rerender } = render(<SpanPicker peaks={peaks} duration={60} start={0} end={10} onChange={vi.fn()} />);

    rerender(<SpanPicker peaks={peaks} duration={60} start={4} end={14} onChange={vi.fn()} />);

    expect(h.region.setOptions).toHaveBeenCalledWith({ start: 4, end: 14 });
  });

  it('destroys the waveform when it leaves the screen', () => {
    const { unmount } = render(<SpanPicker peaks={[0.5]} duration={60} start={0} end={10} onChange={vi.fn()} />);

    unmount();

    expect(h.wave.destroy).toHaveBeenCalledTimes(1);
  });
});

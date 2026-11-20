import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js';
import WaveSurfer from 'wavesurfer.js';
import { useEffect, useRef } from 'react';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { clampSpan } from './span';

// La región del tramo: violeta suave, para que la onda se lea debajo.
const REGION_COLOR = 'oklch(0.541 0.281 293 / 0.25)';

/**
 * El tramo de origen sobre su onda (spec 010, D-4): una región de 8 a 12 s que se puede arrastrar. La onda sale de los picos del
 * server y no se reproduce aquí. Mover la región avisa con el nuevo inicio y fin; los campos de tiempo mueven la región.
 */
export function SpanPicker({
  peaks,
  duration,
  start,
  end,
  onChange,
}: {
  peaks: number[];
  duration: number;
  start: number;
  end: number;
  onChange: (start: number, end: number) => void;
}): React.JSX.Element {
  const container = useRef<HTMLDivElement>(null);
  const region = useRef<{ start: number; end: number; setOptions: (options: { start: number; end: number }) => void } | null>(
    null,
  );
  // Lo último que pintó el padre. Se guarda en un efecto, no al pintar: la onda lo lee al crearse.
  const latest = useRef({ start, end, onChange });
  useEffect(() => {
    latest.current = { start, end, onChange };
  });

  // Una onda nueva por archivo: se crea y se destruye con los picos y la duración.
  useEffect(() => {
    if (!container.current) return;
    const regions = RegionsPlugin.create();
    const wave = WaveSurfer.create({
      container: container.current,
      peaks: [peaks],
      duration,
      height: 64,
      waveColor: 'oklch(0.705 0.015 286)',
      progressColor: 'oklch(0.541 0.281 293)',
      normalize: true,
      plugins: [regions],
    });
    region.current = regions.addRegion({
      start: latest.current.start,
      end: latest.current.end,
      drag: true,
      resize: true,
      color: REGION_COLOR,
    });
    regions.on('region-updated', (updated) => {
      const next = clampSpan(updated.start, updated.end, duration);
      if (next.start !== updated.start || next.end !== updated.end) updated.setOptions(next);
      latest.current.onChange(next.start, next.end);
    });
    return () => {
      region.current = null;
      wave.destroy();
    };
  }, [peaks, duration]);

  // Los campos mueven la región cuando cambian; si ya está ahí, no se toca.
  useEffect(() => {
    const current = region.current;
    if (current && (current.start !== start || current.end !== end)) current.setOptions({ start, end });
  }, [start, end]);

  return <UIStack ref={container} className="min-w-0" />;
}

import { useEffect, useRef } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { UIStack } from '@/shared/components/atoms/UIStack';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js';
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.js';
import ZoomPlugin from 'wavesurfer.js/dist/plugins/zoom.js';

import { type Cut, editCut, toggleCut } from './cuts';

const ON_COLOR = 'rgba(220, 38, 38, 0.35)';
const OFF_COLOR = 'rgba(120, 120, 120, 0.25)';

// Reemplaza las regiones por las de la lista: un corte activo es rojo y un corte desactivado, gris.
function drawCuts(plugin: ReturnType<typeof RegionsPlugin.create>, cuts: Cut[]): void {
  plugin.clearRegions();
  cuts.forEach((cut, index) => {
    plugin.addRegion({
      id: String(index),
      start: cut.start,
      end: cut.end,
      color: cut.enabled ? ON_COLOR : OFF_COLOR,
      drag: true,
      resize: true,
    });
  });
}

export interface ReviewWaveProps {
  media: HTMLMediaElement | null;
  peaks: number[];
  duration: number;
  cuts: Cut[];
  selected: number;
  onCutsChange: (cuts: Cut[]) => void;
  onSelect: (index: number) => void;
}

/**
 * La onda de la revisión (spec 013, D-6). Cada corte es una región roja arrastrable por sus bordes; un clic la selecciona
 * y la activa o desactiva. La línea de tiempo marca los segundos y el zoom sigue la rueda. La onda usa el medio de la
 * pantalla, así que sigue su reproducción sin lógica extra.
 */
export function ReviewWave({ media, peaks, duration, cuts, selected, onCutsChange, onSelect }: ReviewWaveProps): React.JSX.Element {
  const container = useRef<HTMLDivElement>(null);
  const regions = useRef<ReturnType<typeof RegionsPlugin.create> | null>(null);
  // Los oyentes de las regiones leen siempre la lista actual, sin reengancharse en cada cambio.
  const latest = useRef({ cuts, onCutsChange, onSelect });

  useEffect(() => {
    latest.current = { cuts, onCutsChange, onSelect };
  });

  useEffect(() => {
    // Este efecto corre después de montar: el contenedor existe siempre.
    const plugin = RegionsPlugin.create();
    const instance = WaveSurfer.create({
      container: container.current as HTMLElement,
      media: media ?? undefined,
      peaks: [peaks],
      duration,
      height: 96,
      waveColor: 'oklch(0.705 0.015 286)',
      progressColor: 'oklch(0.541 0.281 293)',
      normalize: true,
      plugins: [plugin, TimelinePlugin.create(), ZoomPlugin.create()],
    });
    plugin.on('region-updated', (region) => {
      const { cuts: current, onCutsChange: change } = latest.current;
      change(editCut(current, Number(region.id), region.start, region.end));
    });
    plugin.on('region-clicked', (region) => {
      const index = Number(region.id);
      latest.current.onSelect(index);
      latest.current.onCutsChange(toggleCut(latest.current.cuts, index));
    });
    regions.current = plugin;
    drawCuts(plugin, latest.current.cuts);
    return () => {
      regions.current = null;
      instance.destroy();
    };
  }, [media, peaks, duration]);

  useEffect(() => {
    if (regions.current) drawCuts(regions.current, cuts);
  }, [cuts]);

  return <UIStack ref={container} data-selected={selected} className="w-full" />;
}

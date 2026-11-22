// Línea de tiempo del editor (spec 017, AC-7): zoom, posiciones, selección por rango, mover la selección y el imán.
import { describe, expect, it } from 'vitest';

import {
  ZOOM_LEVELS,
  clipRect,
  moveClips,
  pxToTime,
  selectInRange,
  snapCandidates,
  timeToPx,
  zoomIn,
  zoomOut,
} from '@/features/editor/model/timeline';
import type { Clip, Doc } from '@/features/editor/model/types';

const clip = (id: string, track: string, start: number, length: number): Clip => ({
  id,
  track,
  src: `media/${id}.wav`,
  src_in: 0,
  src_out: length,
  start,
  gain_db: 0,
  fade_in: 0,
  fade_out: 0,
});

const doc = (clips: Clip[]): Doc => ({
  version: 1,
  name: 'demo',
  sample_rate: 48000,
  tracks: [
    { id: 't1', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80 },
    { id: 't2', kind: 'audio', name: 'Música', volume_db: 0, mute: false, solo: false, locked: false, height: 80 },
  ],
  clips,
  markers: [{ id: 'm1', t: 9, label: 'corte', color: '#f00' }],
});

describe('zoom de la línea de tiempo (AC-7)', () => {
  it('acerca y aleja por niveles y se queda en el último y el primero', () => {
    expect(zoomIn(40)).toBe(80);
    expect(zoomOut(40)).toBe(20);
    expect(zoomIn(ZOOM_LEVELS[ZOOM_LEVELS.length - 1])).toBe(ZOOM_LEVELS[ZOOM_LEVELS.length - 1]);
    expect(zoomOut(ZOOM_LEVELS[0])).toBe(ZOOM_LEVELS[0]);
  });
});

describe('tiempo y píxeles', () => {
  it('convierten de ida y vuelta', () => {
    expect(timeToPx(2.5, 40)).toBe(100);
    expect(pxToTime(100, 40)).toBe(2.5);
  });

  it('un clip ocupa su inicio y su duración a la escala del zoom', () => {
    expect(clipRect(clip('c1', 't1', 2, 3), 10)).toEqual({ left: 20, width: 30 });
  });
});

describe('selección y movimiento', () => {
  it('selecciona los clips que se cruzan con el rango de tiempo, no los demás', () => {
    const clips = [clip('a', 't1', 0, 2), clip('b', 't1', 5, 2), clip('c', 't2', 1, 1)];

    expect(selectInRange(clips, 1.5, 5.5)).toEqual(['a', 'b', 'c']);
    expect(selectInRange(clips, 2.5, 4.5)).toEqual([]);
  });

  it('mover la selección mueve cada clip y respeta el hueco de su pista', () => {
    const base = doc([clip('a', 't1', 0, 2), clip('b', 't1', 5, 2)]);

    const moved = moveClips(base, ['a'], 1);
    expect(moved.clips.find((c) => c.id === 'a')?.start).toBe(1);

    // Moverla 4 s la pondría encima de «b»: queda pegada al borde libre más cercano.
    const blocked = moveClips(base, ['a'], 4);
    const start = blocked.clips.find((c) => c.id === 'a')?.start ?? -1;
    expect(start + 2 <= 5 || start >= 7).toBe(true);
  });

  it('ignora ids de clip que ya no están en el documento', () => {
    const base = doc([clip('a', 't1', 0, 2)]);

    expect(moveClips(base, ['missing'], 1)).toEqual(base);
  });

  it('mueve los clips seleccionados juntos sin bloquearse entre sí', () => {
    const base = doc([clip('a', 't1', 0, 1), clip('b', 't1', 1, 1)]);

    expect(moveClips(base, ['a', 'b'], 1).clips.map(({ start }) => start)).toEqual([1, 2]);
  });

  it('conserva el bloque y lo coloca en el borde libre más cercano', () => {
    const base = doc([clip('a', 't1', 0, 1), clip('b', 't1', 2, 1), clip('wall', 't1', 4, 1)]);

    expect(moveClips(base, ['a', 'b'], 4).clips.map(({ start }) => start)).toEqual([3, 5, 4]);
  });
});

describe('imán de la línea de tiempo (D-8)', () => {
  it('los candidatos son el 0, el cabezal, los marcadores y los bordes de los clips que no se mueven', () => {
    const base = doc([clip('a', 't1', 0, 2), clip('b', 't1', 5, 2)]);

    expect(snapCandidates(base, ['b'], 3.5)).toEqual(expect.arrayContaining([0, 2, 3.5, 9]));
    expect(snapCandidates(base, ['b'], 3.5)).not.toEqual(expect.arrayContaining([5, 7]));
  });
});

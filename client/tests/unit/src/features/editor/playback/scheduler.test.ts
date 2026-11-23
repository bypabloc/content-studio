import { describe, expect, it, vi } from 'vitest';

import { activeClips, audibleClips, gainAt, gainRamps, positionAt, shouldCorrectDrift, sourceTimeAt } from '@/features/editor/playback/scheduler';
import type { Clip, Doc, Track } from '@/features/editor/model/types';

function clip(id: string, track: string, start: number, srcIn = 0, srcOut = 4): Clip {
  return { id, track, src: `${id}.wav`, src_in: srcIn, src_out: srcOut, start, gain_db: 0, fade_in: 0, fade_out: 0 };
}

function makeTrack(id: string, values: Partial<Track> = {}): Track {
  return { id, kind: 'audio', name: id, volume_db: 0, mute: false, solo: false, locked: false, height: 80, ...values };
}

function doc(clips: Clip[] = [clip('a', 'voice', 0), clip('b', 'music', 2)]): Doc {
  return { version: 1, name: 'preview', sample_rate: 48000, tracks: [makeTrack('voice'), makeTrack('music')], clips, markers: [] };
}

describe('scheduler de vista previa', () => {
  it('selecciona solo los clips activos y excluye mute/solo igual que el render', () => {
    const value = doc();
    expect(audibleClips(value).map(({ clip: item }) => item.id)).toEqual(['a', 'b']);
    value.tracks[0].solo = true;
    expect(audibleClips(value).map(({ clip: item }) => item.id)).toEqual(['a']);
    expect(activeClips(value, 2).map(({ clip: item }) => item.id)).toEqual(['a']);

    value.tracks[0].mute = true;
    expect(activeClips(value, 2)).toEqual([]);
  });

  it('usa el intervalo de la fuente desde el inicio del clip y deja fuera el extremo final', () => {
    const item = clip('a', 'voice', 3, 5, 9);
    expect(activeClips(doc([item]), 1)).toEqual([expect.objectContaining({ clip: item })]);
    expect(sourceTimeAt(item, 3.5)).toBe(5.5);
    expect(activeClips(doc([item]), 9.01)).toEqual([]);
  });

  it('programa rampas lineales de fade en ganancia con el volumen combinado', () => {
    const item = { ...clip('a', 'voice', 2, 0, 4), gain_db: -6, fade_in: 0.5, fade_out: 0.5 };
    const voice = makeTrack('voice', { volume_db: -6 });
    const peak = 10 ** (-12 / 20);

    expect(gainRamps(item, voice)).toEqual([
      [2, 0],
      [2.5, peak],
      [5.5, peak],
      [6, 0],
    ]);
    expect(gainAt(item, voice, 2.25)).toBeCloseTo(peak / 2);
    expect(gainAt(item, voice, 5.75)).toBeCloseTo(peak / 2);
  });

  it('conserva la ganancia base sin fades y silencia fuera del intervalo', () => {
    const item = clip('a', 'voice', 2);
    const voice = makeTrack('voice', { volume_db: -6 });

    expect(gainRamps(item, voice)).toEqual([]);
    expect(gainAt(item, voice, 2)).toBeCloseTo(10 ** (-6 / 20));
    expect(gainAt(item, voice, 1)).toBe(0);
    expect(gainAt(item, voice, 6)).toBe(0);
  });

  it('calcula la posición con reloj simulado y la limita a la duración', () => {
    let clock = 10;
    const now = vi.fn(() => clock);
    const started = now();
    clock = 11.25;
    expect(positionAt(3, started, now(), 6)).toBe(4.25);
    clock = 20;
    expect(positionAt(3, started, now(), 6)).toBe(6);
    expect(now).toHaveBeenCalledTimes(3);
  });

  it('corrige solo una deriva mayor a 40 ms', () => {
    expect(shouldCorrectDrift(2, 2.04)).toBe(false);
    expect(shouldCorrectDrift(2, 2.041)).toBe(true);
  });
});

// Espejo de server/tests/unit/src/content_studio/editor/test_ops.py: las mismas fixtures dan el mismo resultado.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { apply } from '@/features/editor/model/ops';
import type { Clip, Doc, Op } from '@/features/editor/model/types';

// Vitest corre desde client/: las fixtures compartidas viven en server/tests/fixtures/editor.
const FIXTURES = join(process.cwd(), '..', 'server', 'tests', 'fixtures', 'editor');
const load = (name: string) => JSON.parse(readFileSync(join(FIXTURES, name), 'utf-8'));
const OPS = readdirSync(FIXTURES)
  .filter((name) => name.startsWith('ops-'))
  .sort();

describe('operaciones del editor (AC-1)', () => {
  it.each(OPS)('%s da los ids y los campos de expected, y no toca la entrada', (name) => {
    const fixture = load(name);
    const before = structuredClone(fixture.doc);

    const result: Doc = apply(fixture.doc as Doc, fixture.op as Op);

    const expected = fixture.expected;
    expect(result.clips.map((clip: Clip) => clip.id).sort()).toEqual([...expected.ids].sort());
    const byId = new Map(result.clips.map((clip: Clip) => [clip.id, clip]));
    for (const [clipId, fields] of Object.entries<Record<string, unknown>>(expected.clips)) {
      const clip = byId.get(clipId) as unknown as Record<string, unknown>;
      expect(Object.fromEntries(Object.keys(fields).map((key) => [key, clip[key]]))).toEqual(fields);
    }
    const tracks = new Map(result.tracks.map((track) => [track.id, track]));
    for (const [trackId, fields] of Object.entries<Record<string, unknown>>(expected.tracks ?? {})) {
      const track = tracks.get(trackId) as unknown as Record<string, unknown>;
      expect(Object.fromEntries(Object.keys(fields).map((key) => [key, track[key]]))).toEqual(fields);
    }
    if (expected.track_ids !== undefined) expect(result.tracks.map((track) => track.id)).toEqual(expected.track_ids);
    if (expected.markers !== undefined) expect(result.markers).toEqual(expected.markers);
    if (expected.transitions !== undefined) expect(result.transitions).toEqual(expected.transitions);
    for (const clipId of expected.without_link ?? []) {
      expect(result.clips.find((clip) => clip.id === clipId)).not.toHaveProperty('link');
    }
    expect(fixture.doc).toEqual(before);
  });

  it('rechaza una operación desconocida con su código', () => {
    const doc: Doc = { version: 2, name: 'x', sample_rate: 48000, canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' }, tracks: [], clips: [], markers: [], transitions: [] };

    expect(() => apply(doc, { type: 'nope' } as unknown as Op)).toThrow('unknown_op');
  });

  it('rechaza una actualización de pista inexistente', () => {
    const doc: Doc = { version: 2, name: 'x', sample_rate: 48000, canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' }, tracks: [], clips: [], markers: [], transitions: [] };

    expect(() => apply(doc, { type: 'setTrack', id: 'missing', changes: { mute: true } })).toThrow('unknown_track');
  });

  it('actualiza un fundido sin cambiar el borde omitido', () => {
    const doc: Doc = {
      version: 2,
      name: 'x',
      sample_rate: 48000,
      canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' },
      tracks: [],
      clips: [{ id: 'c1', track: 't1', src: 'a.wav', src_in: 0, src_out: 2, start: 0, gain_db: 0, fade_in: 0.1, fade_out: 0.2 }],
      markers: [],
      transitions: [],
    };

    expect(apply(doc, { type: 'setFade', id: 'c1', fade_in: 0.5 }).clips[0]).toMatchObject({ fade_in: 0.5, fade_out: 0.2 });
    expect(apply(doc, { type: 'setFade', id: 'c1', fade_out: 0.7 }).clips[0]).toMatchObject({ fade_in: 0.1, fade_out: 0.7 });
  });
});

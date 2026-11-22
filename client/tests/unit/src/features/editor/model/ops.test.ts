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
    expect(fixture.doc).toEqual(before);
  });

  it('rechaza una operación desconocida con su código', () => {
    const doc: Doc = { version: 1, name: 'x', sample_rate: 48000, tracks: [], clips: [], markers: [] };

    expect(() => apply(doc, { type: 'nope' } as unknown as Op)).toThrow('unknown_op');
  });
});

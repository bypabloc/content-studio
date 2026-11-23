// Espejo de server/tests/unit/src/content_studio/editor/test_keyframes.py: fixtures compartidas Python/TypeScript.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { segments, valueAt } from '@/features/editor/model/keyframes';

const FIXTURES = join(process.cwd(), '..', 'server', 'tests', 'fixtures', 'editor');
const CASES = [
  'keyframes-after-duration.json',
  'keyframes-ease-in-out.json',
  'keyframes-empty.json',
  'keyframes-hold.json',
  'keyframes-linear.json',
  'keyframes-zero-duration.json',
];

describe('interpolación de keyframes (AC-1)', () => {
  it.each(CASES)('%s coincide con sus muestras y segmentos compartidos', (name) => {
    const fixture = JSON.parse(readFileSync(join(FIXTURES, name), 'utf-8'));

    for (const sample of fixture.samples) {
      expect(valueAt(fixture.keyframes, sample.t, fixture.default)).toBeCloseTo(sample.expected, 9);
    }
    expect(segments(fixture.keyframes, fixture.clip_duration)).toEqual(fixture.segments);
  });
});

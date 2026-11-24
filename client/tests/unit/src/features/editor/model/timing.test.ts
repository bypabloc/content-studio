// Paridad con server/tests/unit/src/content_studio/editor/test_timing.py y las fixtures compartidas.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { atempoFilters, clipDuration, sourceTime } from '@/features/editor/model/timing';

const FIXTURES = join(process.cwd(), '..', 'server', 'tests', 'fixtures', 'editor');
const CASES = readdirSync(FIXTURES)
  .filter((name) => name.startsWith('timing-'))
  .sort()
  .flatMap((name) => JSON.parse(readFileSync(join(FIXTURES, name), 'utf-8')).cases);

describe('velocidad de clips (AC-1/4)', () => {
  it.each(CASES)('$id coincide con la fixture compartida', (fixture) => {
    expect(clipDuration(fixture.clip)).toBeCloseTo(fixture.duration, 10);
    expect(sourceTime(fixture.clip, fixture.timeline_time)).toBeCloseTo(fixture.source_time, 10);
    expect(atempoFilters(fixture.clip.speed)).toEqual(fixture.atempo);
  });

  it.each([0.249, 4.001, Number.NaN, true])('rechaza la velocidad invalida %s', (speed) => {
    expect(() => atempoFilters(speed as number)).toThrow('speed');
  });
});

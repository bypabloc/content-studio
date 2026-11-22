// Espejo de server/tests/unit/src/content_studio/editor/test_project.py: validación y duración con las mismas fixtures.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { duration, validate } from '@/features/editor/model/validate';
import type { Doc } from '@/features/editor/model/types';

const FIXTURES = join(process.cwd(), '..', 'server', 'tests', 'fixtures', 'editor');
const load = (name: string) => JSON.parse(readFileSync(join(FIXTURES, name), 'utf-8'));
const INVALID = readdirSync(FIXTURES)
  .filter((name) => name.startsWith('invalid-'))
  .sort();

describe('validación del proyecto (AC-1)', () => {
  it.each(INVALID)('%s devuelve exactamente sus códigos de error', (name) => {
    const fixture = load(name);

    const codes = validate(fixture.doc as Doc).map((error) => error.code).sort();

    expect(codes).toEqual([...fixture.errors].sort());
  });

  it('acepta el documento de una fixture válida', () => {
    expect(validate(load('ops-move-sin-pisar.json').doc as Doc)).toEqual([]);
  });

  it('la duración es el final del clip que más tarde termina; sin clips, 0', () => {
    const doc = load('ops-delete-sin-ripple.json').doc as Doc;

    expect(duration(doc)).toBe(12);
    expect(duration({ ...doc, clips: [] })).toBe(0);
  });
});

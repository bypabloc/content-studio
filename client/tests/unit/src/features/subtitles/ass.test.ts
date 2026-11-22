/**
 * Espejo del ASS (spec 014, D-9; AC-9): para los mismos cues y el mismo estilo, el client escribe el ASS del server, línea por línea.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { toAss } from '@/features/subtitles/ass';

// Vitest corre desde client/: los golden del server viven en server/tests/fixtures/subtitles.
const FIXTURES = join(process.cwd(), '..', 'server', 'tests', 'fixtures', 'subtitles');

function load(name: string): { input: { doc: unknown; style: unknown; play_res: [number, number] }; golden: string } {
  const input = JSON.parse(readFileSync(join(FIXTURES, `${name}.json`), 'utf-8'));
  // Git guarda LF; en Windows el archivo puede llegar con CRLF.
  const golden = readFileSync(join(FIXTURES, `${name}.ass`), 'utf-8').replace(/\r\n/g, '\n');
  return { input, golden };
}

describe('toAss', () => {
  it.each(['classic', 'minimal', 'karaoke', 'reels'])('escribe el mismo ASS que el server para %s', (name) => {
    const { input, golden } = load(name);

    expect(toAss(input.doc as never, input.style as never, input.play_res)).toBe(golden);
  });
});

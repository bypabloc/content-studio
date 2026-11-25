/**
 * Espejo del ASS (spec 014, D-9; AC-9): para los mismos cues y el mismo estilo, el client escribe el ASS del server, línea por línea.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { type DocIn, type StyleIn, toAss } from '@/features/subtitles/ass';

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

const STYLE: StyleIn = {
  font: 'Arial', size: 48, bold: false, color: '#ffffff', outline_color: '#000000', outline: 2, shadow: 0,
  back_box: null, position: 'bottom', margin_v: 40, uppercase: false, mode: 'classic', highlight_color: '#FFD400', pop: false,
};
const SPEAKERS = { SPEAKER_00: { name: 'Ana', color: '#2563eb' }, SPEAKER_01: { name: 'Luis', color: '#dc2626' } };
const SPOKEN: DocIn = {
  cues: [
    { start: 0, end: 1.5, text: 'hola mundo', speaker: 'SPEAKER_00', words: [
      { start: 0, end: 0.5, text: 'hola', keyword: null }, { start: 0.5, end: 1, text: 'mundo', keyword: null },
    ] },
    { start: 1.5, end: 3, text: 'buenas', speaker: 'SPEAKER_01', words: [{ start: 1.5, end: 3, text: 'buenas', keyword: null }] },
  ],
  speakers: SPEAKERS,
};

describe('toAss with speakers', () => {
  it('paints each classic event with its speaker colour, where the server puts it', () => {
    const ass = toAss(SPOKEN, { ...STYLE, mode: 'classic' });

    expect(ass).toContain('Default,,0,0,0,,{\\1c&HEB6325&}hola mundo');
    expect(ass).toContain('Default,,0,0,0,,{\\1c&H2626DC&}buenas');
  });

  it('paints the social events with the speaker colour and keeps the highlight colour', () => {
    const ass = toAss(SPOKEN, { ...STYLE, mode: 'social' });
    const events = ass.split('\n').filter((line) => line.startsWith('Dialogue:'));

    expect(events.length).toBeGreaterThan(0);
    expect(events.every((line) => line.includes(',,{\\1c&HEB6325&}') || line.includes(',,{\\1c&H2626DC&}'))).toBe(true);
    expect(ass).toContain('\\c&H00D4FF&');
  });

  it('leaves karaoke as it was without speakers', () => {
    const plain: DocIn = { cues: SPOKEN.cues.map((cue) => ({ ...cue, speaker: undefined })) };

    expect(toAss(SPOKEN, { ...STYLE, mode: 'karaoke' })).toBe(toAss(plain, { ...STYLE, mode: 'karaoke' }));
  });
});

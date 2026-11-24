import { describe, expect, it } from 'vitest';

import { deleteCue, mergeCues, setCueText, splitCue, toggleKeyword, type DocEdit, trackDoc } from '@/features/subtitles/cues';

const word = (start: number, end: number, text: string) => ({ start, end, text, keyword: null });

function doc(): DocEdit {
  return {
    version: 1,
    source: { path: 'charla.mp4', kind: 'file' },
    language: 'es',
    style: {},
    tracks: {},
    cues: [
      { id: 1, start: 0, end: 2, text: 'hola a todos', words: [word(0, 0.5, 'hola'), word(0.5, 1, 'a'), word(1, 2, 'todos')] },
      { id: 2, start: 2.5, end: 4, text: 'buenas tardes', words: [word(2.5, 3, 'buenas'), word(3, 4, 'tardes')] },
    ],
  };
}

describe('cues', () => {
  it('splits a cue at a word and renumbers the ids', () => {
    const next = splitCue(doc(), 0, 2);

    expect(next.cues.map((cue) => [cue.id, cue.text, cue.start, cue.end])).toEqual([
      [1, 'hola a', 0, 1],
      [2, 'todos', 1, 2],
      [3, 'buenas tardes', 2.5, 4],
    ]);
  });

  it('merges a cue with the next one', () => {
    const next = mergeCues(doc(), 0);

    expect(next.cues).toHaveLength(1);
    expect(next.cues[0]).toMatchObject({ id: 1, start: 0, end: 4, text: 'hola a todos buenas tardes' });
  });

  it('keeps the timings when the word count stays and spreads the new words when it changes', () => {
    const same = setCueText(doc(), 0, 'hola a amigos');

    expect(same.cues[0].words.map((w) => [w.start, w.end, w.text])).toEqual([
      [0, 0.5, 'hola'],
      [0.5, 1, 'a'],
      [1, 2, 'amigos'],
    ]);

    const more = setCueText(doc(), 1, 'buenas tardes a todos').cues[1].words;

    expect(more).toHaveLength(4);
    expect(more[0].start).toBe(2.5);
    expect(more.at(-1)?.end).toBe(4);
  });

  it('deletes a cue and toggles a keyword on a word', () => {
    expect(deleteCue(doc(), 0).cues.map((cue) => cue.id)).toEqual([1]);

    const flagged = toggleKeyword(doc(), 0, 1, { color: '#FF5555' });

    expect(flagged.cues[0].words[1].keyword).toEqual({ color: '#FF5555' });
    expect(toggleKeyword(flagged, 0, 1, { color: '#FF5555' }).cues[0].words[1].keyword).toBeNull();
  });
});

describe('trackDoc', () => {
  it('uses the cues of a translated track and spreads each cue time over its words', () => {
    const base = { version: 1, source: { path: 'a.mp4', kind: 'file' }, language: 'es', style: {}, cues: [] };
    const doc = { ...base, tracks: { pt: [{ id: 1, start: 0, end: 2, text: 'olá  mundo' }] } };

    const shown = trackDoc(doc, 'pt');

    expect(shown.language).toBe('pt');
    expect(shown.cues[0].words.map((word) => word.text)).toEqual(['olá', 'mundo']);
    expect(shown.cues[0].words.at(-1)?.end).toBe(2);
    expect(trackDoc(doc, 'fr')).toBe(doc);
  });
});

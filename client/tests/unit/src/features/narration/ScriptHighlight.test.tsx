import { describe, expect, it } from 'vitest';
import { markSegments } from '@/features/narration/ScriptHighlight';

function issueAt(line: number, col: number, length: number, message = 'regla') {
  return { rule: 6, code: 'semicolon', line, col, length, params: {}, message };
}

describe('markSegments', () => {
  it('sin avisos, el texto entero va sin marcar', () => {
    expect(markSegments('Hola.', [])).toEqual([{ text: 'Hola.' }]);
  });

  it('ubica el aviso por línea y columna, contando los saltos de las líneas anteriores', () => {
    expect(markSegments('Uno.\nHola; mundo', [issueAt(2, 5, 1, 'regla 6')])).toEqual([
      { text: 'Uno.\nHola' },
      { text: ';', message: 'regla 6' },
      { text: ' mundo' },
    ]);
  });

  it('un aviso que se solapa con otro ya marcado se omite', () => {
    expect(markSegments('Hola', [issueAt(1, 1, 3, 'primero'), issueAt(1, 2, 1, 'segundo')])).toEqual([
      { text: 'Hol', message: 'primero' },
      { text: 'a' },
    ]);
  });
});

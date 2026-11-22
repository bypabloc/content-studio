import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { CueList } from '@/features/subtitles/CueList';
import type { DocEdit } from '@/features/subtitles/cues';
import { t } from '@/shared/i18n/t';

const word = (start: number, end: number, text: string) => ({ start, end, text, keyword: null });

const doc: DocEdit = {
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

describe('CueList', () => {
  afterEach(cleanup);

  it('shows each cue text in an editable field and passes the edit up', () => {
    const onChange = vi.fn();
    render(<CueList doc={doc} onChange={onChange} />);

    fireEvent.change(screen.getByDisplayValue('hola a todos'), { target: { value: 'hola a amigos' } });

    expect(onChange.mock.calls[0][0].cues[0].text).toBe('hola a amigos');
  });

  it('splits a cue and merges it with the next one through its buttons', () => {
    const onChange = vi.fn();
    render(<CueList doc={doc} onChange={onChange} />);

    fireEvent.click(screen.getAllByRole('button', { name: t('subtitles.cues.split') })[0]);
    expect(onChange.mock.calls[0][0].cues).toHaveLength(3);

    fireEvent.click(screen.getAllByRole('button', { name: t('subtitles.cues.merge') })[0]);
    expect(onChange.mock.calls[1][0].cues).toHaveLength(1);
  });

  it('marks a word as a keyword with a click on its chip', () => {
    const onChange = vi.fn();
    render(<CueList doc={doc} onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: 'todos' }));

    expect(onChange.mock.calls[0][0].cues[0].words[2].keyword).toEqual({ color: '#FF5555' });
  });

  it('shows a word that is already a keyword as pressed', () => {
    const marked: DocEdit = {
      ...doc,
      cues: [{ ...doc.cues[0], words: [{ ...doc.cues[0].words[0], keyword: { color: '#FF5555' } }, ...doc.cues[0].words.slice(1)] }],
    };
    render(<CueList doc={marked} onChange={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'hola' }).getAttribute('aria-pressed')).toBe('true');
  });
});

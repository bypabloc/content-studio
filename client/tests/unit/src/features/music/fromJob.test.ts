import { describe, expect, it } from 'vitest';

import { musicDraft } from '@/features/music/fromJob';

describe('musicDraft (spec 020, AC-7)', () => {
  it('con presets devuelve los estilos, la duración y las opciones avanzadas', () => {
    expect(
      musicDraft({ id: 1, kind: 'music', params: { style: ['lofi-chill', 3], duration: 45, variants: 2, no_lm: true, evaluate: false, retries: 0 } }),
    ).toEqual({ styles: ['lofi-chill'], free: null, duration: 45, variants: 2, noLm: true, evaluate: false, retries: 0 });
  });

  it('con tonalidad, BPM o compás es texto libre; lo que falta queda en null', () => {
    expect(musicDraft({ id: 2, kind: 'music', params: { style: ['piano suave'], bpm: 90 } })).toEqual({
      styles: [],
      free: { caption: 'piano suave', key: null, bpm: 90, timeSignature: '4' },
      duration: null,
      variants: null,
      noLm: null,
      evaluate: null,
      retries: null,
    });
    expect(musicDraft({ id: 3, kind: 'music', params: { style: 'x', key: 'C major', time_signature: '3' } }).free).toEqual({
      caption: '',
      key: 'C major',
      bpm: null,
      timeSignature: '3',
    });
  });
});

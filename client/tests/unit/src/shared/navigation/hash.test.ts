import { afterEach, describe, expect, it } from 'vitest';

import { hashParams, openSection } from '@/shared/navigation/hash';

afterEach(() => {
  window.location.hash = '';
});

describe('navegación por el hash (spec 016, D-4)', () => {
  it('openSection escribe la sección y sus parámetros en el hash', () => {
    openSection('mix', { voice: 'D:/media/voz.wav' });

    expect(window.location.hash).toBe('#/mix?voice=D%3A%2Fmedia%2Fvoz.wav');
  });

  it('hashParams lee los parámetros de la sección actual', () => {
    window.location.hash = '#/music?match=D%3A%2Fmedia%2Fvoz.wav&tail=2';

    expect(hashParams().get('match')).toBe('D:/media/voz.wav');
    expect(hashParams().get('tail')).toBe('2');
  });

  it('sin parámetros, hashParams no trae ninguno', () => {
    window.location.hash = '#/mix';

    expect([...hashParams().keys()]).toEqual([]);
  });
});

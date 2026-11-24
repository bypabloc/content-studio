import { describe, expect, it } from 'vitest';

import { destinationsFor, openInEditor, sendTo } from '@/shared/navigation/sendTo';

describe('sendTo', () => {
  it('limita los destinos según el tipo de medio', () => {
    expect(destinationsFor('audio')).toEqual(['convert', 'normalize', 'subtitles', 'mix']);
    expect(destinationsFor('video')).toEqual(['convert', 'subtitles', 'mix']);
  });

  it('abre un destino con la ruta como parámetro path', () => {
    sendTo('normalize', 'C:\\Studio\\voice take.wav');

    expect(window.location.hash).toBe('#/normalize?path=C%3A%5CStudio%5Cvoice+take.wav');
  });

  it('abre el Editor con todos los medios como valores add repetidos', () => {
    openInEditor(['C:\\Studio\\voice.wav', 'C:\\Studio\\video.mp4']);

    const query = new URLSearchParams(window.location.hash.split('?')[1]);
    expect(window.location.hash.split('?')[0]).toBe('#/editor');
    expect(query.getAll('add')).toEqual(['C:\\Studio\\voice.wav', 'C:\\Studio\\video.mp4']);
  });
});

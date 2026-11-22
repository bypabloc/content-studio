import { describe, expect, it } from 'vitest';

import {
  advancedFields,
  advancedOptions,
  type Catalog,
  convertJob,
  formatOptions,
  qualityOptions,
  rateOptions,
} from '@/features/convert/convertOptions';

const catalog: Catalog = {
  formats: [
    { id: 'mp3', kind: 'audio' },
    { id: 'wav', kind: 'audio' },
    { id: 'mp4-h264', kind: 'video' },
    { id: 'gif', kind: 'gif' },
  ],
  presets: [
    { id: 'reels', width: 1080, height: 1920, fps: 30, reframe: 'center', recommended: true },
    { id: 'youtube-1080', width: 1920, height: 1080, fps: 30, reframe: 'center', recommended: false },
  ],
};

const original = { channels: 'original', rate: 'original', resolution: 'original', fps: 'original' };

describe('formatOptions', () => {
  it('con audio ofrece solo formatos de audio y Redes, con MP3 ★', () => {
    const options = formatOptions('audio', catalog);

    expect(options.map((option) => option.value)).toEqual(['mp3', 'wav', 'social']);
    expect(options.find((option) => option.recommended)?.value).toBe('mp3');
  });

  it('con video ofrece todos los formatos y Redes al final, con MP4 (H.264) ★', () => {
    const options = formatOptions('video', catalog);

    expect(options.map((option) => option.value)).toEqual(['mp3', 'wav', 'mp4-h264', 'gif', 'social']);
    expect(options.find((option) => option.recommended)?.value).toBe('mp4-h264');
  });

  it('cada opción de formato lleva el nombre de su grupo como pista', () => {
    const audio = formatOptions('audio', catalog).find((option) => option.value === 'mp3');

    expect(audio?.hint).toBe('Audio');
  });
});

describe('calidades y frecuencias', () => {
  it('MP3 ofrece V0, V2, V4 y dos CBR, con V2 ★', () => {
    const options = qualityOptions('mp3');

    expect(options.map((option) => option.value)).toEqual(['vbr-0', 'vbr-2', 'vbr-4', 'cbr-192', 'cbr-320']);
    expect(options.find((option) => option.recommended)?.value).toBe('vbr-2');
  });

  it('el video no tiene calidad: la fija el codificador', () => {
    expect(qualityOptions('mp4-h264')).toEqual([]);
  });

  it('Opus solo ofrece 16 y 48 kHz además de original', () => {
    expect(rateOptions('ogg-opus').map((option) => option.value)).toEqual(['original', '16000', '48000']);
    expect(rateOptions('mp3').map((option) => option.value)).toEqual(['original', '16000', '22050', '44100', '48000']);
  });
});

describe('avanzado', () => {
  it('audio tiene canales y frecuencia; video, resolución y fps; el GIF ninguno', () => {
    expect(advancedFields('mp3')).toEqual(['channels', 'rate']);
    expect(advancedFields('mp4-h264')).toEqual(['resolution', 'fps']);
    expect(advancedFields('gif')).toEqual([]);
  });

  it('un campo en «original» no manda nada; uno elegido manda su número', () => {
    expect(advancedOptions('mp3', original)).toEqual({});
    expect(advancedOptions('mp3', { ...original, channels: '1', rate: '44100' })).toEqual({
      channels: 1,
      sample_rate: 44100,
    });
    expect(advancedOptions('mp4-h264', { ...original, resolution: '720', fps: '30' })).toEqual({
      resolution: 720,
      fps: 30,
    });
  });

  it('las opciones que no aplican al formato no se mandan', () => {
    expect(advancedOptions('mp4-h264', { ...original, channels: '2', rate: '48000' })).toEqual({});
  });
});

describe('convertJob', () => {
  it('un formato de audio manda su calidad y el destino', () => {
    const job = convertJob('a.wav', { format: 'mp3', quality: 'vbr-2', preset: null, advanced: original }, null, catalog);

    expect(job).toEqual({ kind: 'media.convert', params: { input: 'a.wav', target: 'mp3', options: { vbr: 2 } } });
  });

  it('el GIF manda sus fps y su ancho desde la calidad', () => {
    const job = convertJob(
      'a.mp4',
      { format: 'gif', quality: 'gif-15-480', preset: null, advanced: original },
      null,
      catalog,
    );

    expect(job.params).toMatchObject({ target: 'gif', options: { fps: 15, width: 480 } });
  });

  it('Redes manda MP4 H.264 con el tamaño, los fps y el encuadre del preset', () => {
    const job = convertJob(
      'a.mp4',
      { format: 'social', quality: '', preset: 'reels', advanced: original },
      { mode: 'center' },
      catalog,
    );

    expect(job.params).toEqual({
      input: 'a.mp4',
      target: 'mp4-h264',
      options: { width: 1080, height: 1920, fps: 30, reframe: { mode: 'center' } },
    });
  });
});

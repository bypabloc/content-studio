import { describe, expect, it } from 'vitest';

import { MEDIA_EXTENSIONS, baseName, isVideoPath, jobErrorMessage } from '@/shared/media/formats';
import { t } from '@/shared/i18n/t';

describe('extensiones de medios', () => {
  it('aceptan los audios y videos que lee el server', () => {
    expect(MEDIA_EXTENSIONS).toEqual(expect.arrayContaining(['wav', 'mp3', 'mp4', 'mov', 'mkv', 'webm']));
  });

  it('distinguen el video del audio sin importar mayúsculas', () => {
    expect(isVideoPath('/media/clip.MP4')).toBe(true);
    expect(isVideoPath('/media/voz.wav')).toBe(false);
    expect(isVideoPath('/media/sin-extension')).toBe(false);
  });

  it('el nombre del archivo es lo que va después de la última barra, en Windows o en Unix', () => {
    expect(baseName('C:\\media\\clip.mp4')).toBe('clip.mp4');
    expect(baseName('/media/voz.wav')).toBe('voz.wav');
    expect(baseName('voz.wav')).toBe('voz.wav');
  });
});

describe('jobErrorMessage', () => {
  it('un código con texto sin parámetros da su motivo', () => {
    expect(jobErrorMessage('reference_protected')).toBe(t('error.reference_protected'));
  });

  it('un código con parámetros que el trabajo no guarda da el texto genérico, no una llave sin rellenar', () => {
    expect(jobErrorMessage('codec_unavailable')).toBe(t('media.error.generic'));
  });

  it('sin código, o con un código desconocido, da el texto genérico', () => {
    expect(jobErrorMessage(null)).toBe(t('media.error.generic'));
    expect(jobErrorMessage(undefined)).toBe(t('media.error.generic'));
    expect(jobErrorMessage('process_failed_somehow')).toBe(t('media.error.generic'));
  });
});

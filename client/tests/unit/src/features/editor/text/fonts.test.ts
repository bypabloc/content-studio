import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { Api } from '@/shared/api/client';
import { loadFont, loadFonts } from '@/features/editor/text/fonts';

const FONTS = [{ family: 'Inter', styles: ['Regular'], path: 'D:/fonts/Inter-Regular.ttf', bundled: true }];
const api = {
  get: vi.fn().mockResolvedValue(FONTS),
  fileUrl: vi.fn((path: string) => `http://local/files?path=${encodeURIComponent(path)}`),
} as unknown as Api;

let previousFonts: PropertyDescriptor | undefined;
const fontSet = { add: vi.fn() };
const fontFace = { load: vi.fn().mockResolvedValue(undefined) };
const constructFontFace = vi.fn();

class FontFaceStub {
  constructor(family: string, source: string) {
    constructFontFace(family, source);
  }

  async load(): Promise<FontFace> {
    await fontFace.load();
    return fontFace as unknown as FontFace;
  }
}

beforeEach(() => {
  previousFonts = Object.getOwnPropertyDescriptor(document, 'fonts');
  Object.defineProperty(document, 'fonts', { configurable: true, value: fontSet });
  vi.stubGlobal('FontFace', FontFaceStub);
  vi.clearAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
  if (previousFonts) Object.defineProperty(document, 'fonts', previousFonts);
  else Reflect.deleteProperty(document, 'fonts');
});

describe('editor fonts', () => {
  it('AC-2: obtiene las familias OFL y del sistema desde la API de subtítulos', async () => {
    await expect(loadFonts(api)).resolves.toEqual(FONTS);

    expect(api.get).toHaveBeenCalledWith('/subtitles/fonts');
  });

  it('AC-2: carga una familia desde /files y la registra una sola vez', async () => {
    const first = await loadFont(api, 'Inter');
    const second = await loadFont(api, 'Inter');

    expect(first).toBe(true);
    expect(second).toBe(true);
    expect(api.fileUrl).toHaveBeenCalledWith(FONTS[0].path);
    expect(constructFontFace).toHaveBeenCalledWith('Inter', expect.stringContaining('Inter-Regular.ttf'));
    expect(fontFace.load).toHaveBeenCalledTimes(1);
    expect(fontSet.add).toHaveBeenCalledWith(fontFace);
  });

  it('AC-2: informa si una familia dejó de estar disponible', async () => {
    await expect(loadFont(api, 'Missing')).resolves.toBe(false);
  });

  it('reintenta la lista después de un fallo de red', async () => {
    const broken = { get: vi.fn().mockRejectedValue(new Error('offline')) } as unknown as Api;

    await expect(loadFonts(broken)).rejects.toThrow('offline');
    await expect(loadFonts(broken)).rejects.toThrow('offline');

    expect(broken.get).toHaveBeenCalledTimes(2);
  });
});

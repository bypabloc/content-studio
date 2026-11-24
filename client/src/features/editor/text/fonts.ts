import type { Api } from '@/shared/api/client';

export type EditorFont = { family: string; styles: string[]; path: string; bundled: boolean };

const fontsByApi = new WeakMap<Api, Promise<EditorFont[]>>();
const loadedByApi = new WeakMap<Api, Set<string>>();

export async function loadFonts(api: Api): Promise<EditorFont[]> {
  let fonts = fontsByApi.get(api);
  if (!fonts) {
    fonts = api.get<EditorFont[]>('/subtitles/fonts').catch((error: unknown) => {
      fontsByApi.delete(api);
      throw error;
    });
    fontsByApi.set(api, fonts);
  }
  return fonts;
}

export async function loadFont(api: Api, family: string): Promise<boolean> {
  const fonts = await loadFonts(api);
  const font = fonts.find((item) => item.family === family);
  if (!font) return false;
  let loaded = loadedByApi.get(api);
  if (!loaded) {
    loaded = new Set();
    loadedByApi.set(api, loaded);
  }
  if (loaded.has(family)) return true;
  const source = `url(${JSON.stringify(api.fileUrl(font.path))})`;
  const face = await new FontFace(family, source).load();
  document.fonts.add(face);
  loaded.add(family);
  return true;
}

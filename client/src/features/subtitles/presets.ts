import type { StyleIn } from './ass';

export type PresetName = 'classic' | 'reels' | 'karaoke' | 'minimal';

// Espejo de los presets de `subtitles/styles.py` (D-5): la vista previa usa los mismos valores que exportar y quemar.
const BASE: StyleIn = {
  font: 'Arial', // i18n-ignore: nombre de fuente del sistema, no es texto de interfaz
  size: 48,
  bold: false,
  color: '#FFFFFF',
  outline_color: '#000000',
  outline: 3,
  shadow: 0,
  back_box: null,
  position: 'bottom',
  margin_v: 60,
  uppercase: false,
  mode: 'classic',
  words_per_cue: null,
  highlight_color: '#FFD400',
  pop: false,
};

export const BUILTIN_PRESETS: Record<PresetName, StyleIn> = {
  classic: { ...BASE },
  reels: {
    ...BASE,
    font: 'Montserrat ExtraBold', // i18n-ignore: nombre de fuente incluida, no es texto de interfaz
    size: 72,
    bold: true,
    position: 'middle',
    margin_v: 0,
    uppercase: true,
    mode: 'social',
    words_per_cue: 2,
    pop: true,
  },
  karaoke: { ...BASE, mode: 'karaoke' },
  minimal: { ...BASE, size: 36, back_box: '#00000080' },
};

/** El ★ del recomendado (D-5): vertical (relación de aspecto ≤ 0,8) → reels; si no, classic. */
export function recommendedPreset(aspect: number): PresetName {
  return aspect <= 0.8 ? 'reels' : 'classic';
}

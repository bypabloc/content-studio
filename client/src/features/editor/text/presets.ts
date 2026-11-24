import type { TextStyle } from '../model/types';
import { t } from '@/shared/i18n/t';

export const TEXT_PRESETS = ['lower-third', 'title-center', 'caption-bold'] as const;
export type TextPresetName = (typeof TEXT_PRESETS)[number];

const DEFAULT_FONT = 'Arial'; // i18n-ignore: font family name

const PRESETS: Record<TextPresetName, TextStyle> = {
  'lower-third': {
    content: t('editor.text.default_lower_third'), font: DEFAULT_FONT, weight: 700, size: 48, color: '#ffffff',
    stroke: { width: 2, color: '#000000' }, shadow: { x: 0, y: 3, blur: 8, color: '#00000099' },
    box: { color: '#000000aa', padding: 16, radius: 10 }, align: 'left', line_height: 1.2, max_width: 1200,
  },
  'title-center': {
    content: t('editor.text.default_title_center'), font: DEFAULT_FONT, weight: 700, size: 96, color: '#ffffff',
    stroke: { width: 3, color: '#000000' }, shadow: { x: 0, y: 4, blur: 12, color: '#00000099' },
    align: 'center', line_height: 1.1, max_width: 1500,
  },
  'caption-bold': {
    content: t('editor.text.default_caption_bold'), font: DEFAULT_FONT, weight: 700, size: 52, color: '#ffffff',
    stroke: { width: 2, color: '#000000' }, shadow: { x: 0, y: 2, blur: 6, color: '#00000099' },
    box: { color: '#000000aa', padding: 12, radius: 6 }, align: 'center', line_height: 1.15, max_width: 1600,
  },
};

export function createTextStyle(preset: TextPresetName): TextStyle {
  return structuredClone(PRESETS[preset]);
}

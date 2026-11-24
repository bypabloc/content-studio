import type { SelectOption } from '@/shared/components/molecules/UIRecommendedSelect';
import { type MessageKey, t } from '@/shared/i18n/t';

/** La opción «Redes»: no es un formato, es un preset de red (que trae su tamaño, sus fps y el encuadre). */
export const SOCIAL = 'social';
export const FORMAT_KEY = 'select.convert.format';
export const PRESET_KEY = 'select.convert.social';
/** Los presets de red salen en MP4 H.264 (el destino que todas las plataformas reproducen). */
export const SOCIAL_TARGET = 'mp4-h264';

const AUDIO_TARGETS = ['mp3', 'wav', 'flac', 'ogg-opus', 'ogg-vorbis', 'm4a'];

export interface Preset {
  id: string;
  width: number;
  height: number;
  fps: number;
  reframe: string;
  recommended?: boolean;
}

/** Lo que devuelve `GET /catalog/media`: los formatos de salida y los presets de red (uno ★ según la proporción). */
export interface Catalog {
  formats: { id: string; kind: 'audio' | 'video' | 'gif' }[];
  presets: Preset[];
}

/** Lo que el usuario eligió en los selectores avanzados: «original» o un número, como texto. */
export interface Advanced {
  channels: string;
  rate: string;
  resolution: string;
  fps: string;
}

/** La elección de formato de Convertir. `preset` solo cuando el formato es «Redes». */
export interface FormatChoice {
  format: string;
  quality: string;
  preset: string | null;
  advanced: Advanced;
}

/** El encuadre de un preset de red (los cuatro modos de D-3 de la spec 015). */
export type Reframe =
  | { mode: 'center' }
  | { mode: 'manual'; x: number; y: number; w: number; h: number }
  | { mode: 'fit-bars'; color: string }
  | { mode: 'fit-blur'; strength: number }
  | { mode: 'follow-face'; track: string };

/** Las calidades de cada formato de audio y del GIF. Cada una lleva las opciones que recibe el armador de ffmpeg. */
const QUALITY: Record<string, { id: string; options: Record<string, number>; recommended?: boolean }[]> = {
  mp3: [
    { id: 'vbr-0', options: { vbr: 0 } },
    { id: 'vbr-2', options: { vbr: 2 }, recommended: true },
    { id: 'vbr-4', options: { vbr: 4 } },
    { id: 'cbr-192', options: { bitrate: 192 } },
    { id: 'cbr-320', options: { bitrate: 320 } },
  ],
  wav: [
    { id: 'depth-16', options: { depth: 16 }, recommended: true },
    { id: 'depth-24', options: { depth: 24 } },
    { id: 'depth-32', options: { depth: 32 } },
  ],
  flac: [
    { id: 'level-5', options: { level: 5 }, recommended: true },
    { id: 'level-8', options: { level: 8 } },
  ],
  'ogg-opus': [
    { id: 'bitrate-128', options: { bitrate: 128 }, recommended: true },
    { id: 'bitrate-96', options: { bitrate: 96 } },
    { id: 'bitrate-192', options: { bitrate: 192 } },
  ],
  'ogg-vorbis': [
    { id: 'quality-5', options: { quality: 5 }, recommended: true },
    { id: 'quality-3', options: { quality: 3 } },
    { id: 'quality-7', options: { quality: 7 } },
  ],
  m4a: [
    { id: 'bitrate-192', options: { bitrate: 192 }, recommended: true },
    { id: 'bitrate-128', options: { bitrate: 128 } },
    { id: 'bitrate-256', options: { bitrate: 256 } },
  ],
  gif: [
    { id: 'gif-15-480', options: { fps: 15, width: 480 }, recommended: true },
    { id: 'gif-10-320', options: { fps: 10, width: 320 } },
    { id: 'gif-24-720', options: { fps: 24, width: 720 } },
  ],
};

function text(key: string): string {
  return t(key as MessageKey);
}

/** Los formatos que se ofrecen: un audio solo sale a audio (y a «Redes»); un video sale a todo. ★ MP3 o MP4 H.264. */
export function formatOptions(kind: 'audio' | 'video', catalog: Catalog): SelectOption[] {
  const recommended = kind === 'video' ? 'mp4-h264' : 'mp3';
  const formats = catalog.formats
    .filter((format) => kind === 'video' || format.kind === 'audio')
    .map((format) => ({
      value: format.id,
      label: text(`convert.format.${format.id}`),
      recommended: format.id === recommended,
      hint: text(`convert.group.${format.kind}`),
    }));
  return [...formats, { value: SOCIAL, label: text('convert.format.social') }];
}

/** Los presets de red, con el ★ que trae el catálogo (según la proporción de la fuente). */
export function presetOptions(catalog: Catalog): SelectOption[] {
  return catalog.presets.map((preset) => ({
    value: preset.id,
    label: text(`convert.preset.${preset.id}`),
    recommended: preset.recommended,
    hint: `${preset.width}×${preset.height} · ${preset.fps} fps`,
  }));
}

/** Las calidades de un formato; vacías para el video (su calidad la fija el codificador). */
export function qualityOptions(format: string): SelectOption[] {
  return (QUALITY[format] ?? []).map((choice) => ({
    value: choice.id,
    label: text(`convert.quality.${choice.id}`),
    recommended: choice.recommended,
  }));
}

/** Los canales, la frecuencia, la resolución y los fps de «Avanzado»; cada uno empieza en «original». */
export const CHANNEL_OPTIONS: SelectOption[] = [
  { value: 'original', label: text('convert.channels.original'), recommended: true },
  { value: '1', label: text('convert.channels.1') },
  { value: '2', label: text('convert.channels.2') },
];

/** La frecuencia depende del formato: Opus solo codifica 16 kHz y 48 kHz (y 8, 12 y 24, que no se ofrecen). */
export function rateOptions(format: string): SelectOption[] {
  const rates = format === 'ogg-opus' ? ['16000', '48000'] : ['16000', '22050', '44100', '48000'];
  return [
    { value: 'original', label: text('convert.rate.original'), recommended: true },
    ...rates.map((rate) => ({ value: rate, label: text(`convert.rate.${rate}`) })),
  ];
}

export const RESOLUTION_OPTIONS: SelectOption[] = [
  { value: 'original', label: text('convert.resolution.original'), recommended: true },
  ...['2160', '1440', '1080', '720', '480'].map((height) => ({ value: height, label: text(`convert.resolution.${height}`) })),
];

export const FPS_OPTIONS: SelectOption[] = [
  { value: 'original', label: text('convert.fps.original'), recommended: true },
  ...['60', '30', '24'].map((fps) => ({ value: fps, label: text(`convert.fps.${fps}`) })),
];

/** Los campos de «Avanzado» que aplican a un formato: canales y frecuencia en audio; resolución y fps en video. */
export function advancedFields(format: string): ('channels' | 'rate' | 'resolution' | 'fps')[] {
  if (AUDIO_TARGETS.includes(format)) return ['channels', 'rate'];
  return format === 'gif' ? [] : ['resolution', 'fps'];
}

/** Las opciones de «Avanzado» que aplican a un formato; un campo en «original» no manda nada. */
export function advancedOptions(format: string, advanced: Advanced): Record<string, number> {
  const fields = advancedFields(format);
  const options: Record<string, number> = {};
  if (fields.includes('channels') && advanced.channels !== 'original') options.channels = Number(advanced.channels);
  if (fields.includes('rate') && advanced.rate !== 'original') options.sample_rate = Number(advanced.rate);
  if (fields.includes('resolution') && advanced.resolution !== 'original') options.resolution = Number(advanced.resolution);
  if (fields.includes('fps') && advanced.fps !== 'original') options.fps = Number(advanced.fps);
  return options;
}

/** El trabajo `media.convert` de un archivo, con la elección de formato y el encuadre (si es «Redes»). */
export function convertJob(input: string, choice: FormatChoice, reframe: Reframe | null, catalog: Catalog) {
  if (choice.format === SOCIAL) {
    const preset = catalog.presets.find((item) => item.id === choice.preset);
    return {
      kind: 'media.convert',
      params: {
        input,
        target: SOCIAL_TARGET,
        options: { width: preset?.width, height: preset?.height, fps: preset?.fps, reframe },
      },
    };
  }
  const quality = QUALITY[choice.format]?.find((item) => item.id === choice.quality)?.options ?? {};
  return {
    kind: 'media.convert',
    params: { input, target: choice.format, options: { ...quality, ...advancedOptions(choice.format, choice.advanced) } },
  };
}

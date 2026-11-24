/**
 * Espejo del ASS del server (`subtitles/ass.py`, spec 014, D-3 y D-9): la vista previa usa el mismo texto que exportar y quemar.
 * Las funciones son puras. `pyRound` sigue al `round` de Python, que lleva el empate al par.
 */

export interface KeywordIn {
  color?: string | null;
  emoji?: string | null;
}

export interface WordIn {
  start: number;
  end: number;
  text: string;
  keyword?: KeywordIn | null;
}

export interface CueIn {
  start: number;
  end: number;
  text: string;
  words: WordIn[];
}

export interface DocIn {
  cues: CueIn[];
}

export interface StyleIn {
  font: string;
  size: number;
  bold: boolean;
  color: string;
  outline_color: string;
  outline: number;
  shadow: number;
  back_box: string | null;
  position: 'bottom' | 'middle' | 'top';
  margin_v: number;
  uppercase: boolean;
  mode: 'classic' | 'social' | 'karaoke';
  words_per_cue?: number | null;
  highlight_color: string;
  pop: boolean;
}

type PlayRes = [number, number];

const LINE_CHARS = 42;
const POP = '\\t(0,80,\\fscx115\\fscy115)\\t(80,160,\\fscx100\\fscy100)';
const ALIGNMENT: Record<StyleIn['position'], number> = { bottom: 2, middle: 5, top: 8 };

/** `round` de Python: el empate va al número par (2,5 pasa a 2). */
export function pyRound(value: number): number {
  const floor = Math.floor(value);
  const rest = value - floor;
  if (rest > 0.5) return floor + 1;
  if (rest < 0.5) return floor;
  return floor % 2 === 0 ? floor : floor + 1;
}

const pad2 = (value: number): string => String(value).padStart(2, '0');
const codePoints = (text: string): number => [...text].length;

/** Tiempo de ASS, H:MM:SS.cc (centésimas). */
function assTime(seconds: number): string {
  const hundredths = pyRound(seconds * 100);
  const hours = Math.floor(hundredths / 360_000);
  const minutes = Math.floor((hundredths % 360_000) / 6_000);
  const secs = Math.floor((hundredths % 6_000) / 100);
  return `${hours}:${pad2(minutes)}:${pad2(secs)}.${pad2(hundredths % 100)}`;
}

/** Color `#RRGGBB` o `#RRGGBBAA` a `&HBBGGRR&` (o `&HAABBGGRR&` con opacidad). */
export function assColor(value: string): string {
  const digits = value.replace(/^#+/, '');
  const red = digits.slice(0, 2);
  const green = digits.slice(2, 4);
  const blue = digits.slice(4, 6);
  const alpha = digits.length === 8 ? (255 - parseInt(digits.slice(6, 8), 16)).toString(16).padStart(2, '0') : '';
  return `&H${alpha}${blue}${green}${red}&`.toUpperCase();
}

/** Parte las palabras en renglones de hasta `maxChars` caracteres, sin cortar ninguna. */
export function wrapLines(words: string[], maxChars: number): string[] {
  const lines: string[] = [];
  let line = '';
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (codePoints(candidate) <= maxChars || !line) {
      line = candidate;
    } else {
      lines.push(line);
      line = word;
    }
  }
  if (line) lines.push(line);
  return lines;
}

/** Palabra sin llaves (las llaves son etiquetas de ASS) y en mayúsculas si el estilo lo pide. */
function cleanText(word: string, style: StyleIn): string {
  const cleaned = word.replace(/\{/g, '(').replace(/\}/g, ')');
  return style.uppercase ? cleaned.toUpperCase() : cleaned;
}

function header(style: StyleIn, [width, height]: PlayRes): string[] {
  const fill = assColor(style.color);
  const outline = assColor(style.outline_color);
  const back = style.back_box ? assColor(style.back_box) : assColor('#000000');
  const borderStyle = style.back_box ? 3 : 1;
  const bold = style.bold ? -1 : 0;
  return [
    '[Script Info]',
    'ScriptType: v4.00+', // i18n-ignore: encabezado del formato ASS, no es texto de interfaz
    `PlayResX: ${width}`,
    `PlayResY: ${height}`,
    'WrapStyle: 0',
    'ScaledBorderAndShadow: yes', // i18n-ignore: encabezado del formato ASS, no es texto de interfaz
    '',
    '[V4+ Styles]',
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, ' + // i18n-ignore: encabezado del formato ASS
      'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, ' + // i18n-ignore: encabezado del formato ASS
      'MarginR, MarginV, Encoding', // i18n-ignore: encabezado del formato ASS
    `Style: Default,${style.font},${style.size},${fill},${fill},${outline},${back},${bold},0,0,0,100,100,0,0,` + // i18n-ignore: línea de estilo del formato ASS
      `${borderStyle},${style.outline},${style.shadow},${ALIGNMENT[style.position]},40,40,${style.margin_v},1`,
    '',
    '[Events]',
    'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text', // i18n-ignore: encabezado del formato ASS
  ];
}

function dialogue(start: number, end: number, text: string): string {
  return `Dialogue: 0,${assTime(start)},${assTime(end)},Default,,0,0,0,,${text}`;
}

function classic(cue: CueIn, style: StyleIn): string {
  const words = cue.text.split(/\s+/).filter(Boolean).map((word) => cleanText(word, style));
  return dialogue(cue.start, cue.end, wrapLines(words, LINE_CHARS).join('\\N'));
}

/** Un Dialogue por palabra activa: el cue entero, con esa palabra en el color de resaltado (o el de su palabra clave) y el pop. */
function social(cue: CueIn, style: StyleIn): string[] {
  const fill = assColor(style.color);
  const highlight = assColor(style.highlight_color);
  return cue.words.map((active) => {
    const parts = cue.words.map((word) => {
      let text = cleanText(word.text, style);
      const keyword = word.keyword;
      if (word === active) {
        const color = keyword?.color ? assColor(keyword.color) : highlight;
        const pop = style.pop ? POP : '';
        text = `{\\c${color}${pop}}${text}{\\c${fill}}`;
      }
      if (keyword?.emoji) text = `${text} ${keyword.emoji}`;
      return text;
    });
    return dialogue(active.start, active.end, parts.join(' '));
  });
}

function karaoke(cue: CueIn, style: StyleIn): string {
  const parts = cue.words.map((word) => `{\\kf${pyRound((word.end - word.start) * 100)}}${cleanText(word.text, style)}`);
  return dialogue(cue.start, cue.end, parts.join(' '));
}

/** ASS del documento con el estilo dado. `playRes` es la resolución del video (1920×1080 si es solo audio). */
export function toAss(doc: DocIn, style: StyleIn, playRes: PlayRes = [1920, 1080]): string {
  const lines = header(style, playRes);
  for (const cue of doc.cues) {
    if (style.mode === 'social') lines.push(...social(cue, style));
    else if (style.mode === 'karaoke') lines.push(karaoke(cue, style));
    else lines.push(classic(cue, style));
  }
  return `${lines.join('\n')}\n`;
}

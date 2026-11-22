/**
 * Edición del documento de subtítulos en el client (spec 014, D-1 y D-9). Cada función devuelve un documento nuevo; el
 * server guarda el resultado con PUT /subtitles/{id}.
 */

export interface KeywordEdit {
  color?: string | null;
  emoji?: string | null;
}

export interface WordEdit {
  start: number;
  end: number;
  text: string;
  keyword?: KeywordEdit | null;
}

export interface CueEdit {
  id: number;
  start: number;
  end: number;
  text: string;
  words: WordEdit[];
}

export interface DocEdit {
  version: number;
  source: { path: string; kind: string };
  language: string;
  cues: CueEdit[];
  style: Record<string, unknown>;
  tracks: Record<string, unknown>;
}

const joinWords = (words: WordEdit[]): string => words.map((word) => word.text).join(' ');

/** Los ids van de 1 en adelante, en orden, después de cada cambio. */
function withCues(doc: DocEdit, cues: CueEdit[]): DocEdit {
  return { ...doc, cues: cues.map((cue, index) => ({ ...cue, id: index + 1 })) };
}

/** Reparte el intervalo entre las palabras nuevas, en proporción a sus caracteres. */
function spread(start: number, end: number, texts: string[]): WordEdit[] {
  const total = texts.reduce((sum, text) => sum + text.length, 0) || 1;
  let cursor = start;
  return texts.map((text, index) => {
    const stop = index === texts.length - 1 ? end : cursor + ((end - start) * text.length) / total;
    const word: WordEdit = { start: cursor, end: stop, text, keyword: null };
    cursor = stop;
    return word;
  });
}

/** El texto nuevo del cue. Si conserva la cantidad de palabras, sus tiempos y palabras clave se quedan. */
export function setCueText(doc: DocEdit, index: number, text: string): DocEdit {
  const cues = doc.cues.map((cue, position) => {
    if (position !== index) return cue;
    const texts = text.split(/\s+/).filter(Boolean);
    const words =
      texts.length === cue.words.length
        ? cue.words.map((word, at) => ({ ...word, text: texts[at] }))
        : spread(cue.start, cue.end, texts);
    return { ...cue, text, words };
  });
  return withCues(doc, cues);
}

/** Divide el cue antes de la palabra `atWord` (por defecto, a la mitad). Sin una palabra a cada lado, no cambia. */
export function splitCue(doc: DocEdit, index: number, atWord?: number): DocEdit {
  const cue = doc.cues[index];
  if (!cue) return doc;
  const at = atWord ?? Math.floor(cue.words.length / 2);
  if (at < 1 || at >= cue.words.length) return doc;
  const head = cue.words.slice(0, at);
  const tail = cue.words.slice(at);
  const first: CueEdit = { ...cue, end: head[head.length - 1].end, text: joinWords(head), words: head };
  const second: CueEdit = { ...cue, start: tail[0].start, text: joinWords(tail), words: tail };
  return withCues(doc, [...doc.cues.slice(0, index), first, second, ...doc.cues.slice(index + 1)]);
}

/** Une el cue con el siguiente. */
export function mergeCues(doc: DocEdit, index: number): DocEdit {
  const first = doc.cues[index];
  const second = doc.cues[index + 1];
  if (!first || !second) return doc;
  const merged: CueEdit = {
    ...first,
    end: second.end,
    text: `${first.text} ${second.text}`,
    words: [...first.words, ...second.words],
  };
  return withCues(doc, [...doc.cues.slice(0, index), merged, ...doc.cues.slice(index + 2)]);
}

export function deleteCue(doc: DocEdit, index: number): DocEdit {
  return withCues(
    doc,
    doc.cues.filter((_, position) => position !== index),
  );
}

/** Marca la palabra como clave con ese color y emoji; si ya lo era, la quita. */
export function toggleKeyword(doc: DocEdit, index: number, wordIndex: number, keyword: KeywordEdit): DocEdit {
  const cues = doc.cues.map((cue, position) => {
    if (position !== index) return cue;
    const words = cue.words.map((word, at) => {
      if (at !== wordIndex) return word;
      const same = word.keyword?.color === keyword.color && word.keyword?.emoji === keyword.emoji;
      return { ...word, keyword: same ? null : keyword };
    });
    return { ...cue, words };
  });
  return { ...doc, cues };
}

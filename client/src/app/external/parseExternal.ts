/**
 * Enlaces `content-studio://` (spec 031, D-1 y D-2). Función pura: valida con una lista blanca y no abre, navega ni
 * llama a la API. Lo que no cabe en la lista es un error (AC-4); el hook decide qué mostrar.
 */

export const SCHEME = 'content-studio://';
export const MAX_URL_LENGTH = 4096;

/** Las secciones que `open/<sección>` acepta: las de `app/nav.ts` (la prueba de sincronía está en parseExternal.test.ts). */
export const OPEN_SECTIONS = [
  'narration',
  'music',
  'cleaner',
  'subtitles',
  'convert',
  'normalize',
  'mix',
  'editor',
  'library',
  'voices',
  'catalog',
  'engines',
  'settings',
] as const;

/** Lo que `new/<tipo>` rellena y los únicos parámetros que acepta cada tipo. */
export const NEW_PARAMS = {
  narration: ['text', 'voice', 'style'],
  music: ['style', 'duration'],
  'media.convert': ['input', 'target'],
} as const;

export type NewType = keyof typeof NEW_PARAMS;

export type ExternalRequest =
  | { kind: 'open'; section: string }
  | { kind: 'job' | 'library'; id: number }
  | { kind: 'new'; type: NewType; params: Record<string, string> };

/** Por qué un enlace no es válido: un código, nunca un texto (el aviso lo pone el catálogo, `deeplink.invalid`). */
export type ExternalErrorCode =
  | 'too_long'
  | 'unreadable'
  | 'unknown_action'
  | 'unknown_section'
  | 'bad_id'
  | 'unknown_type'
  | 'unknown_param';

export interface ExternalError {
  kind: 'error';
  code: ExternalErrorCode;
}

/** Primer enlace del argv. `null` si no hay ninguno (un arranque normal). */
export function parseExternal(argv: readonly string[]): ExternalRequest | ExternalError | null {
  const url = argv.find((arg) => arg.startsWith(SCHEME));
  return url === undefined ? null : parseUrl(url);
}

function parseUrl(url: string): ExternalRequest | ExternalError {
  if (url.length > MAX_URL_LENGTH) return failure('too_long');
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return failure('unreadable');
  }
  const parts = parsed.pathname.split('/').filter(Boolean);
  switch (parsed.hostname) {
    case 'open':
      return openRequest(parts);
    case 'job':
    case 'library':
      return idRequest(parsed.hostname, parts);
    case 'new':
      return newRequest(parts, parsed.searchParams);
    default:
      return failure('unknown_action');
  }
}

function openRequest(parts: string[]): ExternalRequest | ExternalError {
  const [section] = parts;
  if (parts.length !== 1 || !(OPEN_SECTIONS as readonly string[]).includes(section)) {
    return failure('unknown_section');
  }
  return { kind: 'open', section };
}

function idRequest(kind: 'job' | 'library', parts: string[]): ExternalRequest | ExternalError {
  const [id] = parts;
  if (parts.length !== 1 || !/^[1-9]\d*$/.test(id)) return failure('bad_id');
  return { kind, id: Number(id) };
}

function newRequest(parts: string[], query: URLSearchParams): ExternalRequest | ExternalError {
  const [type] = parts;
  if (parts.length !== 1 || !(Object.keys(NEW_PARAMS) as string[]).includes(type)) {
    return failure('unknown_type');
  }
  const allowed: readonly string[] = NEW_PARAMS[type as NewType];
  const params: Record<string, string> = {};
  for (const [name, value] of query) {
    if (!allowed.includes(name)) return failure('unknown_param');
    params[name] = value;
  }
  return { kind: 'new', type: type as NewType, params };
}

function failure(code: ExternalErrorCode): ExternalError {
  return { kind: 'error', code };
}

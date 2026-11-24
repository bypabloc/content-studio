import { getLocale } from '@/shared/i18n/locale';
import { type MessageKey, t } from '@/shared/i18n/t';

import type { Filters, Scope } from './types';

export const EMPTY_FILTERS: Filters = {
  q: '',
  content: false,
  kind: '',
  mediaType: '',
  starred: false,
  tag: '',
  since: '',
  length: '',
  sort: 'date',
};

/** Rangos de duración en segundos de los chips. */
const LENGTHS: Record<string, [number | null, number | null]> = {
  short: [null, 60],
  medium: [60, 300],
  long: [300, null],
};

/** Días hacia atrás de los chips de fecha. */
const SINCE_DAYS: Record<string, number> = { today: 0, week: 7, month: 30 };

/** `AAAA-MM-DD` de hace `days` días, en la hora local. */
function dayAgo(days: number, now: Date): string {
  const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - days);
  return `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(day.getDate()).padStart(2, '0')}`;
}

/** La consulta de `GET /library` para los filtros, el alcance y la página. */
export function libraryQuery(filters: Filters, scope: Scope, page: number, now = new Date()): string {
  const query = new URLSearchParams({ sort: filters.sort, page: String(page), page_size: '200' });
  if (filters.q.trim()) query.set('q', filters.q.trim());
  if (filters.q.trim() && filters.content) query.set('content', 'true');
  if (filters.kind) query.set('kind', filters.kind);
  if (filters.mediaType) query.set('media_type', filters.mediaType);
  if (filters.starred) query.set('starred', 'true');
  if (filters.tag) query.set('tag', filters.tag);
  if (filters.since in SINCE_DAYS) query.set('from', dayAgo(SINCE_DAYS[filters.since], now));
  const [min, max] = LENGTHS[filters.length] ?? [null, null];
  if (min !== null) query.set('min_dur', String(min));
  if (max !== null) query.set('max_dur', String(max));
  if (scope.type === 'generated') query.set('origin', 'job');
  if (scope.type === 'folder') query.set('folder', String(scope.id));
  if (scope.type === 'project') query.set('project', String(scope.id));
  return query.toString();
}

/** `m:ss` (o `h:mm:ss`); un guion si no hay duración. */
export function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—';
  const total = Math.round(seconds);
  const [hours, minutes, rest] = [Math.floor(total / 3600), Math.floor((total % 3600) / 60), total % 60];
  const tail = `${String(rest).padStart(2, '0')}`;
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${tail}` : `${minutes}:${tail}`;
}

/** Bytes en B, KB, MB o GB (base 1024), con el separador del idioma activo. */
export function formatSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB']; // i18n-ignore: símbolos de unidades, iguales en los tres idiomas
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const digits = unit === 0 || value >= 100 ? 0 : 1;
  return `${value.toLocaleString(getLocale(), { maximumFractionDigits: digits })} ${units[unit]}`;
}

/** Fecha corta del archivo (segundos desde la época) en el idioma activo. */
export function formatDate(mtime: number): string {
  return new Date(mtime * 1000).toLocaleDateString(getLocale());
}

/** Nombre visible del tipo de un ítem (`library.kind.<tipo>`); un tipo sin texto se muestra tal cual. */
export function kindLabel(kind: string): string {
  return t(`library.kind.${kind}` as MessageKey);
}

/** Texto del botón «Mandar a <sección>». */
export function sendLabel(section: string): string {
  return t(`library.send.${section}` as MessageKey);
}

/** La sección que abre «Editar y repetir» según el tipo del ítem; null si no tiene una. */
export function repeatSection(kind: string): string | null {
  const sections: Record<string, string> = {
    narration: 'narration',
    music: 'music',
    clean: 'cleaner',
    subtitles: 'subtitles',
    convert: 'convert',
    mix: 'mix',
  };
  return sections[kind] ?? null;
}

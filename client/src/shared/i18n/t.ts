import type catalog from '@messages/es.json';
import { CATALOGS } from './catalogs';
import { getLocale } from './locale';

export type MessageKey = keyof typeof catalog;

/** ¿Hay texto para la clave en el catálogo de español (el que tiene todas las claves)? */
export function hasMessage(key: string): boolean {
  return key in CATALOGS.es;
}

/** Tipos de los ids que tienen etiqueta (`label.<tipo>.<id>` en el catálogo, spec 007, D-7). */
export type LabelKind = 'narration.style' | 'narration.engine' | 'music.style' | 'music.model' | 'music.category';

/** Nombre o nota de un estilo, motor o modelo en el idioma activo. Un id sin etiqueta se muestra tal cual. */
export function label(kind: LabelKind, id: string): string {
  return t(`label.${kind}.${id}` as MessageKey);
}

/**
 * Texto visible en el idioma activo. `{nombre}` se reemplaza por el parámetro. Sin texto en ese idioma, usa español;
 * sin texto en ninguno, devuelve la clave tal cual para que se note en pantalla.
 */
export function t(key: MessageKey, params: Record<string, string | number> = {}): string {
  const template: string | undefined = CATALOGS[getLocale()]?.[key] ?? CATALOGS.es[key];
  if (template === undefined) return key;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => String(params[name] ?? match));
}

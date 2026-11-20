import catalog from '@messages/es.json';
import { CATALOGS } from './catalogs';
import { getLocale } from './locale';

export type MessageKey = keyof typeof catalog;

/** ¿Hay texto para la clave en el catálogo de español (el que tiene todas las claves)? */
export function hasMessage(key: string): boolean {
  return key in CATALOGS.es;
}

/**
 * Texto visible en el idioma activo. `{nombre}` se reemplaza por el parámetro. Sin texto en ese idioma, usa español;
 * sin texto en ninguno, devuelve la clave tal cual para que se note en pantalla.
 */
export function t(key: MessageKey, params: Record<string, string | number> = {}): string {
  const template: string | undefined = CATALOGS[getLocale()][key] ?? CATALOGS.es[key];
  if (template === undefined) return key;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => String(params[name] ?? match));
}

import { useSyncExternalStore } from 'react';
import { loadCatalog, LOCALES, type Locale } from './catalogs';

/** `system` sigue la lista de idiomas del sistema; las demás fijan el idioma. */
export type LanguagePreference = 'system' | Locale;

// La misma clave que `ui.language` en la tabla settings: la caché solo adelanta el valor del server (D-6).
const CACHE_KEY = 'ui.language';
const PREFERENCES: readonly string[] = ['system', ...LOCALES];

/** La elección guardada en caché, para pintar en su idioma antes de la respuesta del server. Sin caché, `system`. */
export function readCachedLanguage(): LanguagePreference {
  try {
    const value = localStorage.getItem(CACHE_KEY) ?? '';
    return PREFERENCES.includes(value) ? (value as LanguagePreference) : 'system';
  } catch {
    return 'system';
  }
}

/** Idioma de una preferencia: el elegido, o con `system` el primero soportado de la lista (español si ninguno). */
export function resolveLocale(preference: LanguagePreference, languages: readonly string[]): Locale {
  if (preference !== 'system') return preference;
  for (const language of languages) {
    const base = language.split('-')[0].toLowerCase();
    const match = LOCALES.find((locale) => locale === base);
    if (match) return match;
  }
  return 'es';
}

let active: Locale = resolveLocale(readCachedLanguage(), navigator.languages);
let changeId = 0;
/** Carga el idioma de la caché antes de que main.tsx pinte la primera vista. */
export const localeReady = loadCatalog(active);
const listeners = new Set<() => void>();

// Al cargar el módulo, <html lang> ya dice el idioma de la caché.
document.documentElement.lang = active;

export function getLocale(): Locale {
  return active;
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Cambia el idioma: `<html lang>` lo sigue, la elección queda en caché y las vistas se vuelven a pintar. */
export async function setLocale(preference: LanguagePreference): Promise<void> {
  const target = resolveLocale(preference, navigator.languages);
  const request = ++changeId;
  await loadCatalog(target);
  if (request !== changeId) return;
  active = target;
  document.documentElement.lang = active;
  try {
    localStorage.setItem(CACHE_KEY, preference);
  } catch {
    // Sin almacenamiento la app cambia igual; solo se pierde el adelanto del siguiente arranque.
  }
  listeners.forEach((listener) => listener());
}

/** El idioma activo; el componente se vuelve a pintar al cambiarlo, sin recargar la ventana. */
export function useLocale(): Locale {
  return useSyncExternalStore(subscribe, getLocale);
}

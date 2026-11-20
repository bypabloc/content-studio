import en from '@messages/en.json';
import es from '@messages/es.json';
import pt from '@messages/pt.json';

/** Idiomas de la app: los de la cabecera Accept-Language del server (spec 007, D-3). */
export const LOCALES = ['es', 'en', 'pt'] as const;
export type Locale = (typeof LOCALES)[number];

/** Los tres catálogos de `server/src/content_studio/messages/`, el mismo archivo que lee el server. */
export const CATALOGS: Record<Locale, Record<string, string>> = { es, en, pt };

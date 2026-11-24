import es from '@messages/es.json';

/** Idiomas de la app: los de la cabecera Accept-Language del server (spec 007, D-3). */
export const LOCALES = ['es', 'en', 'pt'] as const;
export type Locale = (typeof LOCALES)[number];

type Catalog = Record<string, string>;
type LoadedCatalogs = { es: Catalog } & Partial<Record<Exclude<Locale, 'es'>, Catalog>>;

/** El catálogo español queda disponible al arrancar; inglés y portugués se importan cuando se eligen. */
export const CATALOGS: LoadedCatalogs = { es };

const LOADERS: Partial<Record<Locale, () => Promise<Catalog>>> = {
  en: async () => (await import('@messages/en.json')).default,
  pt: async () => (await import('@messages/pt.json')).default,
};
const loading: Partial<Record<Locale, Promise<void>>> = {};

/** Carga el catálogo del idioma antes de activarlo. */
export function loadCatalog(locale: Locale): Promise<void> {
  if (CATALOGS[locale]) return Promise.resolve();
  if (loading[locale]) return loading[locale];
  const loader = LOADERS[locale];
  if (!loader) return Promise.resolve();
  loading[locale] = loader().then((catalog) => {
    CATALOGS[locale] = catalog;
  });
  return loading[locale];
}

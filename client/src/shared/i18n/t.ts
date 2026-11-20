import catalog from '@messages/es.json';

export type MessageKey = keyof typeof catalog;

/** Texto visible del catálogo único (`server/src/content_studio/messages/`). `{nombre}` se reemplaza por el parámetro; una clave inexistente se muestra tal cual. */
export function t(key: MessageKey, params: Record<string, string | number> = {}): string {
  const template: string | undefined = (catalog as Record<string, string>)[key];
  if (template === undefined) return key;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => String(params[name] ?? match));
}

import { useEffect } from 'react';
import { useSetting } from '@/shared/hooks/useSetting';
import { readCachedLanguage, setLocale, type LanguagePreference } from './locale';

/**
 * La preferencia de idioma: la guarda el server en `ui.language`, igual que el tema, y la aplica al idioma activo.
 * Con `system`, el idioma sigue la lista del sistema (spec 007, D-6). Sin respuesta del server, vale la caché local.
 */
export function useLanguage(): [LanguagePreference, (preference: LanguagePreference) => void] {
  const [preference, setPreference] = useSetting<LanguagePreference>('ui.language', readCachedLanguage());
  useEffect(() => setLocale(preference), [preference]);
  return [preference, setPreference];
}

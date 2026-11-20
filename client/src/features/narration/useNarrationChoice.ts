import { useQuery } from '@tanstack/react-query';
import { useApi } from '@/shared/api/context';
import { useSetting } from '@/shared/hooks/useSetting';

// El catálogo lo da `GET /catalog/narration`: es un dict en el server, así que su forma se escribe aquí y la prueba
// del server (`test_catalog.py`) la vigila.
export interface CatalogEngine {
  id: string;
  license: string;
  commercial: boolean;
  installed: boolean;
  recommended: boolean;
  note: string;
  batch: boolean;
}
export interface CatalogStyle {
  id: string;
  recommended: boolean;
}
export interface CatalogVoice {
  id: string;
  language: string;
}
export interface NarrationCatalog {
  engines: CatalogEngine[];
  styles: CatalogStyle[];
  voices: CatalogVoice[];
}

/** El catálogo de narración, en caché: los selectores y la pantalla lo leen sin pedirlo otra vez. */
export function useNarrationCatalog() {
  const api = useApi();
  return useQuery({
    queryKey: ['catalog', 'narration'],
    queryFn: () => api.get<NarrationCatalog>('/catalog/narration'),
  });
}

/** El id recomendado de una lista (o el primero si ninguno lo marca). */
function recommendedId(list: readonly { id: string; recommended?: boolean }[]): string {
  return list.find((item) => item.recommended)?.id ?? list[0]?.id ?? '';
}

/** Lo guardado si sigue en la lista; si no, la recomendada (la misma regla que `UIRecommendedSelect`). */
function effective(stored: string, list: readonly { id: string; recommended?: boolean }[]): string {
  return list.some((item) => item.id === stored) ? stored : recommendedId(list);
}

export interface NarrationChoice {
  engines: CatalogEngine[];
  styles: CatalogStyle[];
  voices: CatalogVoice[];
  model: string;
  style: string;
  voice: string;
  language: string;
  master: string;
  lufs: number;
  seed: number | null;
  batch: number | null;
  evaluate: boolean;
  retries: number;
}

/** Las opciones que se ven en pantalla, ya resueltas: el motor, la voz, el estilo, el idioma y lo avanzado. */
export function useNarrationChoice(): NarrationChoice {
  const { data } = useNarrationCatalog();
  const engines = data?.engines ?? [];
  const styles = data?.styles ?? [];
  const voices = data?.voices ?? [];
  const languages = [{ id: 'es', recommended: true }, { id: 'en', recommended: false }];
  const [storedModel] = useSetting<string>('select.narration.model', recommendedId(engines));
  const [storedStyle] = useSetting<string>('select.narration.style', recommendedId(styles));
  const [storedVoice] = useSetting<string>('select.narration.voice', recommendedId(voices));
  const [storedLanguage] = useSetting<string>('select.narration.language', 'es');
  const [master] = useSetting<string>('narration.master', 'voice');
  const [lufs] = useSetting<number>('narration.lufs', -16);
  const [seed] = useSetting<number | null>('narration.seed', null);
  const [batch] = useSetting<number | null>('narration.batch', null);
  const [evaluate] = useSetting<boolean>('narration.evaluate', false);
  const [retries] = useSetting<number>('narration.retries', 0);
  return {
    engines,
    styles,
    voices,
    model: effective(storedModel, engines),
    style: effective(storedStyle, styles),
    voice: effective(storedVoice, voices),
    language: effective(storedLanguage, languages),
    master,
    lufs,
    seed,
    batch,
    evaluate,
    retries,
  };
}

/**
 * Los parámetros de un trabajo de narración: el texto (o el archivo) y las opciones elegidas. Lo que está apagado
 * (semilla vacía, lote automático, sin evaluar) no viaja.
 */
export function narrationParams(choice: NarrationChoice, input: { text: string } | { file: string[] }) {
  const params: Record<string, unknown> = {
    model: choice.model,
    style: choice.style,
    language: choice.language,
    master: choice.master,
    lufs: choice.lufs,
    ...input,
  };
  if (choice.voice) params.voice = choice.voice;
  if (choice.seed !== null) params.seed = choice.seed;
  if (choice.batch !== null) params.batch = choice.batch;
  if (choice.evaluate) Object.assign(params, { evaluate: true, retries: choice.retries });
  return params;
}

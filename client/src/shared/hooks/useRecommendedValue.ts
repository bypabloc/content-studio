import { useSetting } from '@/shared/hooks/useSetting';

/** Lo que la regla de un selector con recomendado necesita de cada opción. */
export interface RecommendableOption {
  value: string;
  recommended?: boolean;
}

/** El valor sin elección guardada: la opción recomendada, o la primera si ninguna lo es. */
export function recommendedValue(options: readonly RecommendableOption[]): string {
  return options.find((option) => option.recommended)?.value ?? options[0]?.value ?? '';
}

/**
 * La elección efectiva de un selector con recomendado: la guardada en `settingKey` si todavía existe entre las
 * opciones, o la recomendada. Es la misma regla que usa `UIRecommendedSelect`, para que una pantalla conozca el valor
 * que el usuario ve sin tener que esperar a que el selector se lo informe.
 */
export function useRecommendedValue(settingKey: string, options: readonly RecommendableOption[]): [string, (value: string) => void] {
  const recommended = recommendedValue(options);
  const [stored, setStored] = useSetting<string>(settingKey, recommended);
  const value = options.some((option) => option.value === stored) ? stored : recommended;
  return [value, setStored];
}

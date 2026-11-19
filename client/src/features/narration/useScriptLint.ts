import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useApi } from '@/shared/api/context';
import type { components } from '@/shared/api/schema';

export type LintOut = components['schemas']['LintOut'];
export type LintIssue = components['schemas']['IssueOut'];

/** El lint no corre por cada tecla: espera este tiempo sin cambios (AC-6). */
export const LINT_DELAY_MS = 300;

/** El valor con un retraso: cambia solo cuando pasan `delay` ms sin nuevos cambios. */
export function useDebounced<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/** Los avisos del linter del guion (`POST /narration/lint`), pedidos tras una pausa de escritura. */
export function useScriptLint(text: string, narrationStyle: string) {
  const api = useApi();
  const debounced = useDebounced(text, LINT_DELAY_MS);
  return useQuery({
    queryKey: ['narration', 'lint', debounced, narrationStyle],
    queryFn: () => api.post<LintOut>('/narration/lint', { text: debounced, style: narrationStyle }),
    enabled: debounced.trim() !== '',
    placeholderData: keepPreviousData,
  });
}

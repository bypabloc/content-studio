import { useEffect, useState, useSyncExternalStore } from 'react';

/**
 * Valores iniciales de una sección desde un enlace externo (spec 031, AC-3). El hook lo deja aquí y la sección lo aplica y lo
 * consume. Vive fuera del hash porque una sección ya abierta no se vuelve a montar al cambiar el hash.
 */
export type Prefill = Record<string, string>;

const pending = new Map<string, Prefill>();
const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) listener();
}

export function setPrefill(section: string, values: Prefill): void {
  pending.set(section, values);
  notify();
}

/** Devuelve lo que quedó para la sección y lo borra: se aplica una sola vez. */
export function consumePrefill(section: string): Prefill | undefined {
  const values = pending.get(section);
  pending.delete(section);
  notify();
  return values;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Lo que espera la sección, sin consumirlo. */
export function usePrefill(section: string): Prefill | undefined {
  return useSyncExternalStore(subscribe, () => pending.get(section));
}

/**
 * Aplica el valores iniciales de una sección una vez, al llegar (en el render, como `appliedJob` en el resto de las secciones)
 * y lo borra al salir de ella. `apply` solo cambia estado de la propia sección.
 */
export function usePrefillApply(section: string, apply: (values: Prefill) => void): void {
  const prefill = usePrefill(section);
  const [applied, setApplied] = useState<Prefill | undefined>(undefined);
  if (prefill !== undefined && prefill !== applied) {
    setApplied(prefill);
    apply(prefill);
  }
  useEffect(() => () => {
    consumePrefill(section);
  }, [section]);
}

import { listen } from '@tauri-apps/api/event';
import { useEffect, useState } from 'react';

/** Un paso de la preparación de la app instalada y su estado, como los emite `bootstrap.rs` (spec 022, D-2). */
export type BootstrapStep = 'python' | 'sync' | 'seed';
export type BootstrapState = 'running' | 'done' | 'skipped' | 'failed';

interface Progress {
  step: BootstrapStep;
  state: BootstrapState;
  log: string;
}

export interface BootstrapProgress {
  steps: Partial<Record<BootstrapStep, BootstrapState>>;
  log: string | null;
}

/** Los eventos `bootstrap` de Tauri, juntados por paso; en un checkout no llega ninguno. */
export function useBootstrapProgress(): BootstrapProgress {
  const [progress, setProgress] = useState<BootstrapProgress>({ steps: {}, log: null });
  useEffect(() => {
    const stop = listen<Progress>('bootstrap', ({ payload }) =>
      setProgress((current) => ({ steps: { ...current.steps, [payload.step]: payload.state }, log: payload.log })),
    );
    return () => {
      void stop.then((stopListening) => stopListening());
    };
  }, []);
  return progress;
}

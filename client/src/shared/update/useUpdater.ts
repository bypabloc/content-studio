import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useApi } from '@/shared/api/context';
import type { Job } from '@/shared/api/events';
import { t } from '@/shared/i18n/t';

/** Lo que el client usa de una actualización de `tauri-plugin-updater`. */
export interface Update {
  version: string;
  downloadAndInstall(): Promise<void>;
}

/** El updater y el reinicio; las pruebas pasan los suyos. */
export interface UpdaterDeps {
  check(): Promise<Update | null>;
  relaunch(): Promise<void>;
}

export type UpdateState =
  | { kind: 'idle' }
  | { kind: 'checking' }
  | { kind: 'latest' }
  | { kind: 'available'; version: string }
  | { kind: 'waiting'; version: string }
  | { kind: 'installing'; version: string }
  | { kind: 'failed' };

const TAURI: UpdaterDeps = {
  check: async () => (await import('@tauri-apps/plugin-updater')).check(),
  relaunch: async () => (await import('@tauri-apps/plugin-process')).relaunch(),
};

/**
 * Actualizaciones desde el último Release (spec 022, D-6): `check` busca una versión nueva; `install` espera a que no
 * haya trabajos corriendo (los encolados siguen tras reiniciar), descarga, instala y reinicia la app.
 */
export function useUpdater(deps: UpdaterDeps = TAURI) {
  const api = useApi();
  const jobs = useQuery({ queryKey: ['jobs'], queryFn: () => api.get<Job[]>('/jobs') });
  const running = (jobs.data ?? []).filter((job) => job.status === 'running').length;
  const [state, setState] = useState<UpdateState>({ kind: 'idle' });
  const update = useRef<Update | null>(null);

  const check = useCallback(async () => {
    setState({ kind: 'checking' });
    try {
      update.current = await deps.check();
      setState(update.current ? { kind: 'available', version: update.current.version } : { kind: 'latest' });
    } catch {
      setState({ kind: 'failed' });
    }
  }, [deps]);

  const install = useCallback(() => {
    if (update.current) setState({ kind: 'waiting', version: update.current.version });
  }, []);

  useEffect(() => {
    const found = update.current;
    if (state.kind !== 'waiting' || running > 0 || !found) return;
    setState({ kind: 'installing', version: state.version });
    found
      .downloadAndInstall()
      .then(() => deps.relaunch())
      .catch(() => setState({ kind: 'failed' }));
  }, [state, running, deps]);

  return { state, running, check, install };
}

/** El texto del estado, o null si no hay nada que decir. */
export function updateMessage(state: UpdateState, running: number): string | null {
  switch (state.kind) {
    case 'checking':
      return t('update.checking');
    case 'latest':
      return t('update.latest');
    case 'available':
      return t('update.available', { version: state.version });
    case 'waiting':
      return t('update.waiting', { count: running });
    case 'installing':
      return t('update.installing', { version: state.version });
    case 'failed':
      return t('update.failed');
    default:
      return null;
  }
}

import { invoke } from '@tauri-apps/api/core';
import { useCallback, useEffect, useState, type ReactNode } from 'react';
import type { Connection } from '@/shared/api/client';
import { t } from '@/shared/i18n/t';

export const APP_VERSION = '0.1.0';

type Status = { kind: 'starting' } | { kind: 'ready'; connection: Connection } | { kind: 'failed'; code: string };

/** Pantalla de la app: arranca el server (Tauri lo levanta) y muestra el motivo si no arranca, con Reintentar (AC-10). */
export function App() {
  const [status, setStatus] = useState<Status>({ kind: 'starting' });

  const connect = useCallback(() => {
    invoke<Connection>('get_connection')
      .then((connection) => setStatus({ kind: 'ready', connection }))
      .catch((code: unknown) => setStatus({ kind: 'failed', code: String(code) }));
  }, []);

  useEffect(() => {
    connect();
  }, [connect]);

  const retry = () => {
    setStatus({ kind: 'starting' });
    connect();
  };

  if (status.kind === 'starting') {
    return <Screen>{t('server.starting')}</Screen>;
  }
  if (status.kind === 'failed') {
    return (
      <Screen>
        <h1 className="text-2xl font-semibold">{t('server.error.title')}</h1>
        <p className="text-sm text-muted-foreground">{reason(status.code)}</p>
        <button
          type="button"
          onClick={retry}
          className="mt-2 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent"
        >
          {t('server.retry')}
        </button>
      </Screen>
    );
  }
  return (
    <Screen>
      <h1 className="text-2xl font-semibold">{t('app.name')}</h1>
      <p className="text-sm text-muted-foreground">{t('app.version', { version: APP_VERSION })}</p>
    </Screen>
  );
}

function Screen({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen select-none flex-col items-center justify-center gap-2">{children}</main>
  );
}

/** El motivo del código que devuelve `get_connection` (server/errores de arranque de src-tauri). */
function reason(code: string): string {
  switch (code) {
    case 'server_spawn_failed':
      return t('server.spawn_failed');
    case 'server_timeout':
      return t('server.timeout');
    default:
      return t('server.exited');
  }
}

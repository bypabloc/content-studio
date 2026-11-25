import { invoke } from '@tauri-apps/api/core';
import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { BootstrapPage } from '@/bootstrap/BootstrapPage';
import { useBootstrapProgress } from '@/bootstrap/useBootstrapProgress';
import { ApiProvider } from '@/shared/api/context';
import type { Connection } from '@/shared/api/client';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIPage } from '@/shared/components/atoms/UIPage';
import { UIText } from '@/shared/components/atoms/UIText';
import { t } from '@/shared/i18n/t';
import { useLocale } from '@/shared/i18n/locale';
import { Providers } from './Providers';
import { Shell } from './Shell';
import { APP_VERSION } from '@/shared/version';

export { APP_VERSION };

type Status = { kind: 'starting' } | { kind: 'ready'; connection: Connection } | { kind: 'failed'; code: string };

/**
 * La app entera: los proveedores, y dentro la conexión con el server (Tauri lo levanta). Al cambiar el idioma, la raíz
 * se vuelve a montar con la nueva `key`: todo el texto sale en el idioma nuevo, sin recargar la ventana (spec 007, D-5).
 */
export function App() {
  const locale = useLocale();
  return (
    <Providers key={locale}>
      <Connected />
    </Providers>
  );
}

/**
 * Muestra el motivo si el server no arranca, con Reintentar (AC-10); con el server arriba, la app. En la app instalada,
 * `get_connection` prepara antes Python y el venv: mientras tanto, y si falla, la pantalla de preparación (spec 022).
 */
function Connected() {
  const [status, setStatus] = useState<Status>({ kind: 'starting' });
  const progress = useBootstrapProgress();

  const connect = useCallback(() => {
    invoke<Connection>('get_connection')
      .then((connection) => setStatus({ kind: 'ready', connection }))
      .catch((code: unknown) => setStatus({ kind: 'failed', code: String(code) }));
  }, []);

  // Tras una caída (inactividad o cambio de token) la app pide la conexión otra vez: get_connection levanta el server.
  const reconnect = useCallback(async () => {
    const connection = await invoke<Connection>('get_connection');
    setStatus({ kind: 'ready', connection });
    return connection;
  }, []);

  useEffect(() => {
    connect();
  }, [connect]);

  const retry = () => {
    setStatus({ kind: 'starting' });
    connect();
  };

  if (status.kind === 'ready') {
    return (
      <ApiProvider connection={status.connection} reconnect={reconnect}>
        <Shell version={APP_VERSION} />
      </ApiProvider>
    );
  }
  if (status.kind === 'failed' && status.code.startsWith('bootstrap_')) {
    return <BootstrapPage {...progress} failed={status.code} onRetry={retry} />;
  }
  if (status.kind === 'failed') {
    return (
      <Screen>
        <UIText variant="title">{t('server.error.title')}</UIText>
        <UIText variant="caption">{reason(status.code)}</UIText>
        <UIButton variant="secondary" className="mt-2" onClick={retry}>
          {t('server.retry')}
        </UIButton>
      </Screen>
    );
  }
  if (Object.keys(progress.steps).length > 0) {
    return <BootstrapPage {...progress} failed={null} onRetry={retry} />;
  }
  return <Screen>{t('server.starting')}</Screen>;
}

function Screen({ children }: { children: ReactNode }) {
  return <UIPage className="flex-col gap-2 select-none">{children}</UIPage>;
}

/** El motivo del código que devuelve `get_connection` (los errores de arranque de src-tauri). */
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

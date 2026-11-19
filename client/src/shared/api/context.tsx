import { useQueryClient, type QueryClient } from '@tanstack/react-query';
import { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react';
import { tauriAlerts } from '@/shared/notify/alerts';
import { announceFinished } from '@/shared/notify/notify';
import { createApi, type Api, type Connection } from './client';
import { connectEvents } from './events';
import type { components } from './schema';

const ApiContext = createContext<Api | null>(null);

/** Un ajuste de avisos; si nunca se guardó, está activo. */
function alertOn(queryClient: QueryClient, key: string): boolean {
  return queryClient.getQueryData<components['schemas']['SettingOut']>(['settings', key])?.value !== false;
}

/**
 * Da el cliente de la API a los hooks y abre la conexión de eventos (SSE) una vez: cada trabajo que termina
 * avisa según el foco de la ventana y los ajustes de avisos.
 */
export function ApiProvider({ connection, children }: { connection: Connection; children: ReactNode }) {
  const api = useMemo(() => createApi(connection), [connection]);
  const queryClient = useQueryClient();

  useEffect(
    () =>
      connectEvents(connection, queryClient, {
        onFinished: (job) =>
          announceFinished(
            job,
            {
              focused: document.hasFocus(),
              system: alertOn(queryClient, 'notify.system'),
              sound: alertOn(queryClient, 'notify.sound'),
            },
            tauriAlerts,
          ),
      }),
    [connection, queryClient],
  );

  return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>;
}

export function useApi(): Api {
  const api = useContext(ApiContext);
  if (api === null) throw new Error('useApi must be used inside ApiProvider');
  return api;
}

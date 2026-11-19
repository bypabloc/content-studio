import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { createApi, type Api, type Connection } from './client';

const ApiContext = createContext<Api | null>(null);

/** Da el cliente de la API a los hooks de la app. La conexión la entrega Tauri con get_connection. */
export function ApiProvider({ connection, children }: { connection: Connection; children: ReactNode }) {
  const api = useMemo(() => createApi(connection), [connection]);
  return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>;
}

export function useApi(): Api {
  const api = useContext(ApiContext);
  if (api === null) throw new Error('useApi must be used inside ApiProvider');
  return api;
}

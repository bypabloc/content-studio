import { getLocale } from '../i18n/locale';
import { ApiError, type ErrorBody } from './errors';

export interface Connection {
  baseUrl: string;
  token: string;
}

/** Cliente HTTP de la API local: cada llamada lleva el Bearer, y cualquier respuesta que no es 2xx lanza ApiError. */
export function createApi(
  connection: Connection,
  fetcher: typeof fetch = fetch,
  reconnect?: () => Promise<Connection>,
) {
  /** La conexión vigente: cambia cuando la app se reconecta (spec 028, AC-8). */
  let current = connection;

  /** Pide la conexión otra vez (get_connection) y la usa desde ahora; sin reconnect, sigue la misma. */
  async function renew(): Promise<Connection> {
    if (reconnect) current = await reconnect();
    return current;
  }

  /** Con `contentType`, el cuerpo va tal cual con ese tipo (una toma WAV); sin él, va como JSON. */
  async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    contentType?: string,
    extraHeaders: Record<string, string> = {},
    retried = false,
  ): Promise<T> {
    const json = body !== undefined && contentType === undefined;
    let response: Response;
    try {
      response = await fetcher(`${current.baseUrl}${path}`, {
        method,
        headers: {
          Authorization: `Bearer ${current.token}`,
          'Accept-Language': getLocale(),
          ...(json ? { 'Content-Type': 'application/json' } : {}),
          ...(contentType ? { 'Content-Type': contentType } : {}),
          ...extraHeaders,
        },
        body: json ? JSON.stringify(body) : (body as BodyInit | undefined),
      });
    } catch (error) {
      // Fallo de red: el server se durmió por inactividad o cambió de token. Se reconecta y se repite una vez (AC-8).
      if (!reconnect || retried) throw error;
      await renew();
      return request<T>(method, path, body, contentType, extraHeaders, true);
    }
    const data: unknown = await response.json().catch(() => null);
    if (!response.ok) throw new ApiError(response.status, data as Partial<ErrorBody> | null);
    return data as T;
  }

  return {
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body?: unknown, headers?: Record<string, string>) => request<T>('PUT', path, body, undefined, headers),
    patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
    del: <T>(path: string) => request<T>('DELETE', path),
    /** Sube un cuerpo crudo, como la toma WAV del micrófono: no pasa por JSON. */
    upload: <T>(path: string, body: BodyInit | ArrayBufferView, contentType: string) => request<T>('POST', path, body, contentType),
    /** URL de un archivo de out/ para el <audio> o la forma de onda: sin cabeceras, el token va en la consulta. */
    fileUrl: (path: string) =>
      `${current.baseUrl}/files?path=${encodeURIComponent(path)}&token=${encodeURIComponent(current.token)}`,
    /** URL de una ruta que una imagen o un medio pide sin cabeceras (el cuadro de `/media/frame`): el token va en la consulta. */
    queryUrl: (path: string, query: Record<string, string | number>) => {
      const params = new URLSearchParams({ ...Object.fromEntries(Object.entries(query).map(([k, v]) => [k, String(v)])), token: current.token });
      return `${current.baseUrl}${path}?${params}`;
    },
    /** La conexión vigente (cambia al reconectar). */
    get connection(): Connection {
      return current;
    },
    /** Pide la conexión otra vez y la usa desde ahora: el panel la pide tras cambiar el token. */
    reconnect: renew,
  };
}

export type Api = ReturnType<typeof createApi>;

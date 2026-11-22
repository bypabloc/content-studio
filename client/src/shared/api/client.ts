import { getLocale } from '../i18n/locale';
import { ApiError, type ErrorBody } from './errors';

export interface Connection {
  baseUrl: string;
  token: string;
}

/** Cliente HTTP de la API local: cada llamada lleva el Bearer, y cualquier respuesta que no es 2xx lanza ApiError. */
export function createApi(connection: Connection, fetcher: typeof fetch = fetch) {
  /** Con `contentType`, el cuerpo va tal cual con ese tipo (una toma WAV); sin él, va como JSON. */
  async function request<T>(method: string, path: string, body?: unknown, contentType?: string): Promise<T> {
    const json = body !== undefined && contentType === undefined;
    const response = await fetcher(`${connection.baseUrl}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${connection.token}`,
        'Accept-Language': getLocale(),
        ...(json ? { 'Content-Type': 'application/json' } : {}),
        ...(contentType ? { 'Content-Type': contentType } : {}),
      },
      body: json ? JSON.stringify(body) : (body as BodyInit | undefined),
    });
    const data: unknown = await response.json().catch(() => null);
    if (!response.ok) throw new ApiError(response.status, data as Partial<ErrorBody> | null);
    return data as T;
  }

  return {
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
    patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
    del: <T>(path: string) => request<T>('DELETE', path),
    /** Sube un cuerpo crudo, como la toma WAV del micrófono: no pasa por JSON. */
    upload: <T>(path: string, body: BodyInit | ArrayBufferView, contentType: string) => request<T>('POST', path, body, contentType),
    /** URL de un archivo de out/ para el <audio> o la forma de onda: sin cabeceras, el token va en la consulta. */
    fileUrl: (path: string) =>
      `${connection.baseUrl}/files?path=${encodeURIComponent(path)}&token=${encodeURIComponent(connection.token)}`,
    /** URL de una ruta que una imagen o un medio pide sin cabeceras (el cuadro de `/media/frame`): el token va en la consulta. */
    queryUrl: (path: string, query: Record<string, string | number>) => {
      const params = new URLSearchParams({ ...Object.fromEntries(Object.entries(query).map(([k, v]) => [k, String(v)])), token: connection.token });
      return `${connection.baseUrl}${path}?${params}`;
    },
  };
}

export type Api = ReturnType<typeof createApi>;

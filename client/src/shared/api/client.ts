import { ApiError, type ErrorBody } from './errors';

export interface Connection {
  baseUrl: string;
  token: string;
}

/** Cliente HTTP de la API local: cada llamada lleva el Bearer, y cualquier respuesta que no es 2xx lanza ApiError. */
export function createApi(connection: Connection, fetcher: typeof fetch = fetch) {
  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const json = body !== undefined;
    const response = await fetcher(`${connection.baseUrl}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${connection.token}`,
        ...(json ? { 'Content-Type': 'application/json' } : {}),
      },
      body: json ? JSON.stringify(body) : undefined,
    });
    const data: unknown = await response.json().catch(() => null);
    if (!response.ok) throw new ApiError(response.status, data as Partial<ErrorBody> | null);
    return data as T;
  }

  return {
    get: <T>(path: string) => request<T>('GET', path),
    post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
    del: <T>(path: string) => request<T>('DELETE', path),
  };
}

export type Api = ReturnType<typeof createApi>;

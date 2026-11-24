import { hasMessage, t, type MessageKey } from '@/shared/i18n/t';

export interface ErrorBody {
  code: string;
  params: Record<string, unknown>;
  message: string;
}

/**
 * Texto del error: el del catálogo del cliente para su código, en el idioma activo (spec 007, AC-7); si el cliente no
 * conoce el código, el `message` que llegó del server; y sin cuerpo, el texto genérico.
 */
function messageOf(body: Partial<ErrorBody> | null): string {
  const key = `error.${body?.code ?? ''}`;
  if (body?.code && hasMessage(key)) {
    const params = Object.fromEntries(Object.entries(body.params ?? {}).map(([name, value]) => [name, String(value)]));
    return t(key as MessageKey, params);
  }
  return body?.message ?? t('api.unknown_error');
}

/** Error de la API con código (spec 004, D-5): el texto sale del catálogo según el idioma activo. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly params: Record<string, unknown>;

  constructor(status: number, body: Partial<ErrorBody> | null) {
    super(messageOf(body));
    this.name = 'ApiError';
    this.status = status;
    this.code = body?.code ?? 'unknown';
    this.params = body?.params ?? {};
  }
}

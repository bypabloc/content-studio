import { t } from '@/shared/i18n/t';

export interface ErrorBody {
  code: string;
  params: Record<string, unknown>;
  message: string;
}

/** Error de la API con código (spec 004, D-5): `message` llega ya traducido desde el server. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly params: Record<string, unknown>;

  constructor(status: number, body: Partial<ErrorBody> | null) {
    super(body?.message ?? t('api.unknown_error'));
    this.name = 'ApiError';
    this.status = status;
    this.code = body?.code ?? 'unknown';
    this.params = body?.params ?? {};
  }
}

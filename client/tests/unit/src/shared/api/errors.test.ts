import { beforeEach, describe, expect, it } from 'vitest';
import { ApiError } from '@/shared/api/errors';
import { setLocale } from '@/shared/i18n/locale';

describe('ApiError', () => {
  beforeEach(() => setLocale('es'));

  it('muestra el texto de su código en el idioma activo', () => {
    setLocale('en');

    const error = new ApiError(404, { code: 'job_not_found', params: { job_id: 3 }, message: 'No existe el trabajo 3' });

    expect(error.message).toBe('Job 3 does not exist.');
    expect(error.code).toBe('job_not_found');
  });

  it('si el código no tiene texto en el cliente, usa el mensaje del server', () => {
    const error = new ApiError(500, { code: 'codigo_nuevo', params: {}, message: 'Texto del server' });

    expect(error.message).toBe('Texto del server');
  });

  it('sin cuerpo, dice que hubo un error de la API en el idioma activo', () => {
    expect(new ApiError(500, null).message).toBe('Error de la API');
  });
});

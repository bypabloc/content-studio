import { describe, expect, it, vi } from 'vitest';
import { createApi } from '@/shared/api/client';
import { ApiError } from '@/shared/api/errors';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function reply(body: unknown, status = 200) {
  return vi.fn(async () => new Response(JSON.stringify(body), { status }));
}

describe('createApi', () => {
  it('manda el Bearer y la URL completa', async () => {
    const fetcher = reply({ paused: false });
    await createApi(connection, fetcher).get('/queue');

    expect(fetcher).toHaveBeenCalledWith(
      'http://127.0.0.1:9000/queue',
      expect.objectContaining({ method: 'GET', headers: { Authorization: 'Bearer tok' } }),
    );
  });

  it('manda el cuerpo como JSON', async () => {
    const fetcher = reply({ key: 'ui.theme', value: 'dark' });
    await createApi(connection, fetcher).put('/settings/ui.theme', { value: 'dark' });

    expect(fetcher).toHaveBeenCalledWith(
      'http://127.0.0.1:9000/settings/ui.theme',
      expect.objectContaining({
        method: 'PUT',
        body: '{"value":"dark"}',
        headers: { Authorization: 'Bearer tok', 'Content-Type': 'application/json' },
      }),
    );
  });

  it('ante un error con código lanza ApiError con su mensaje', async () => {
    const body = { code: 'job_not_found', params: { job_id: 3 }, message: 'No existe el trabajo 3' };
    const error = await createApi(connection, reply(body, 404))
      .get('/jobs/3')
      .catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: 'job_not_found', message: 'No existe el trabajo 3' });
  });

  it('fileUrl da la URL de un archivo con el token en la consulta, para el <audio> y la forma de onda', () => {
    const url = createApi(connection, reply({})).fileUrl('D:/out/a b.wav');

    expect(url).toBe('http://127.0.0.1:9000/files?path=D%3A%2Fout%2Fa%20b.wav&token=tok');
  });

  it('ante un error sin código (validación de FastAPI) usa el texto genérico del catálogo', async () => {
    const error = await createApi(connection, reply({ detail: [] }, 422))
      .post('/jobs', {})
      .catch((caught: unknown) => caught);

    expect(error).toMatchObject({ status: 422, code: 'unknown', message: 'Error de la API' });
  });
});

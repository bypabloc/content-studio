import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createApi } from '@/shared/api/client';
import { ApiError } from '@/shared/api/errors';
import { setLocale } from '@/shared/i18n/locale';

const connection = { baseUrl: 'http://127.0.0.1:9000', token: 'tok' };

function reply(body: unknown, status = 200) {
  return vi.fn(async () => new Response(JSON.stringify(body), { status }));
}

describe('createApi', () => {
  beforeEach(() => setLocale('es'));

  it('manda el Bearer y la URL completa', async () => {
    const fetcher = reply({ paused: false });
    await createApi(connection, fetcher).get('/queue');

    expect(fetcher).toHaveBeenCalledWith(
      'http://127.0.0.1:9000/queue',
      expect.objectContaining({
        method: 'GET',
        headers: { Authorization: 'Bearer tok', 'Accept-Language': 'es' },
      }),
    );
  });

  it('manda el idioma activo en Accept-Language (AC-7)', async () => {
    setLocale('pt');
    const fetcher = reply({ paused: false });
    await createApi(connection, fetcher).get('/queue');

    expect(fetcher).toHaveBeenCalledWith(
      'http://127.0.0.1:9000/queue',
      expect.objectContaining({ headers: expect.objectContaining({ 'Accept-Language': 'pt' }) }),
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
        headers: { Authorization: 'Bearer tok', 'Accept-Language': 'es', 'Content-Type': 'application/json' },
      }),
    );
  });

  it('ante un error con código lanza ApiError con su mensaje', async () => {
    const body = { code: 'job_not_found', params: { job_id: 3 }, message: 'No existe el trabajo 3' };
    const error = await createApi(connection, reply(body, 404))
      .get('/jobs/3')
      .catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: 'job_not_found', message: 'No existe el trabajo 3.' });
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

  it('patch manda el cuerpo como JSON con el método PATCH (renombrar un perfil, spec 010)', async () => {
    const fetcher = reply({ id: 'spec-010', name: 'Voz' });
    await createApi(connection, fetcher).patch('/voices/profiles/spec-010', { name: 'Voz' });

    expect(fetcher).toHaveBeenCalledWith(
      'http://127.0.0.1:9000/voices/profiles/spec-010',
      expect.objectContaining({
        method: 'PATCH',
        body: '{"name":"Voz"}',
        headers: { Authorization: 'Bearer tok', 'Accept-Language': 'es', 'Content-Type': 'application/json' },
      }),
    );
  });

  it('upload manda el cuerpo tal cual con su tipo de contenido (una toma es un WAV crudo, spec 010)', async () => {
    const wav = new Uint8Array([82, 73, 70, 70]);
    const fetcher = reply({ take: 1 }, 201);
    const data = await createApi(connection, fetcher).upload<{ take: number }>(
      '/voices/profiles/spec-010/takes/expert',
      wav,
      'audio/wav',
    );

    expect(data).toEqual({ take: 1 });
    expect(fetcher).toHaveBeenCalledWith(
      'http://127.0.0.1:9000/voices/profiles/spec-010/takes/expert',
      expect.objectContaining({
        method: 'POST',
        body: wav,
        headers: { Authorization: 'Bearer tok', 'Accept-Language': 'es', 'Content-Type': 'audio/wav' },
      }),
    );
  });
});

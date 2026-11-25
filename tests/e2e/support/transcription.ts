import { apiFixture, type Replies } from './app';

/**
 * Las respuestas de la API de Transcripción (spec 036): un trabajo `transcribe` terminado (id 7), su transcripción y
 * los nombres que la app guarda con `PUT /jobs/7/speakers`, que la transcripción siguiente vuelve a leer.
 */
export function transcriptionReplies(options: { engines?: string; transcript?: string } = {}): Replies {
  const engines = apiFixture<unknown[]>(options.engines ?? 'transcription/engines');
  const transcript = apiFixture<{ speakers: Record<string, unknown> }>(options.transcript ?? 'transcription/transcript-speakers');
  return ({ method, path, body }) => {
    if (method === 'GET' && path === '/engines') return engines;
    if (method === 'POST' && path === '/jobs') return { id: 7 };
    if (method === 'GET' && path === '/jobs/7') return apiFixture('transcription/job-done');
    if (method === 'GET' && path === '/jobs/7/transcript') return transcript;
    if (method === 'PUT' && path === '/jobs/7/speakers') {
      transcript.speakers = body as Record<string, unknown>;
      return body;
    }
    if (method === 'POST' && path === '/jobs/7/transcript/export') return { path: 'D:/out/transcript.txt' };
    if (method === 'POST' && path === '/subtitles/from-transcript') return { id: 9 };
    return undefined;
  };
}

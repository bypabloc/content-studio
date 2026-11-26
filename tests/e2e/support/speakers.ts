import { apiFixture, type Replies } from './app';

/**
 * Las respuestas de la API de Hablantes (spec 037): un trabajo `diarize` terminado (id 7) con su resultado, los nombres que
 * la app guarda con `PUT /jobs/7/speakers` y, tras pedir «Un audio por hablante», los audios separados (`diarize.split`, id 8).
 */
export function speakersReplies(): Replies {
  const diarization = apiFixture<Record<string, unknown> & { speakers: Record<string, unknown> }>('speakers/diarization');
  const split = apiFixture<{ split: Record<string, string> }>('speakers/diarization-split').split;
  let splitReady = false;
  return ({ method, path, body }) => {
    if (method === 'POST' && path === '/jobs') {
      if ((body as { kind: string }).kind === 'diarize.split') {
        splitReady = true;
        return { id: 8 };
      }
      return { id: 7 };
    }
    if (method === 'GET' && path === '/jobs/7') return apiFixture('speakers/job-done');
    if (method === 'GET' && path === '/diarizations/7') return { ...diarization, split: splitReady ? split : null };
    if (method === 'PUT' && path === '/jobs/7/speakers') {
      diarization.speakers = body as Record<string, unknown>;
      return body;
    }
    if (method === 'POST' && path === '/editor/projects/from-diarization') return { project: 'D:/out/editor/charla/project.json' };
    return undefined;
  };
}

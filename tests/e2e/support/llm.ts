import { apiFixture, type Replies } from './app';

/** Las respuestas del asistente (spec 021): su estado, los idiomas y la propuesta de cada tarea, grabadas en _api/llm/. */
export function llmReplies(options: { enabled?: boolean } = {}): Replies {
  const jobs: Record<string, unknown>[] = [];
  return ({ method, path, body }) => {
    if (method === 'GET' && path === '/llm/status') return { ...apiFixture('llm/status'), enabled: options.enabled ?? true };
    if (method === 'GET' && path === '/llm/languages') return apiFixture('llm/languages');
    const kind = (body as { kind?: string } | null)?.kind ?? '';
    if (method === 'POST' && path === '/jobs' && kind.startsWith('llm.')) {
      const job = { id: 900 + jobs.length, kind, status: 'done', params: {}, output_dir: 'C:/fake/out/llm', resource: 'gpu' };
      jobs.push(job);
      return job;
    }
    if (method === 'GET' && path === '/jobs' && jobs.length) return jobs;
    const result = /^\/llm\/jobs\/(\d+)\/result$/.exec(path);
    if (method === 'GET' && result) {
      const job = jobs.find((item) => item.id === Number(result[1]));
      return job ? apiFixture(`llm/${String(job.kind).slice(4)}`) : undefined;
    }
    return undefined;
  };
}

/** Varias respuestas propias en orden: gana la primera que responde. */
export function combine(...replies: Replies[]): Replies {
  return (call) => {
    for (const reply of replies) {
      const answer = reply(call);
      if (answer !== undefined) return answer;
    }
    return undefined;
  };
}

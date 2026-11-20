import { readFileSync } from 'node:fs';
import { expect, type Page } from '@playwright/test';
import type { Binary, Replies } from './app';

/** Un WAV mudo de `seconds` a 8 kHz: el reproductor de la prueba lo puede tocar de verdad (AC-10). */
function silentWav(seconds = 1): Buffer {
  const rate = 8000;
  const samples = rate * seconds;
  const header = Buffer.alloc(44);
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + samples, 4);
  header.write('WAVE', 8);
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(rate, 24);
  header.writeUInt32LE(rate, 28);
  header.writeUInt16LE(1, 32);
  header.writeUInt16LE(8, 34);
  header.write('data', 36);
  header.writeUInt32LE(samples, 40);
  return Buffer.concat([header, Buffer.alloc(samples, 128)]);
}

function fixture(name: string): Record<string, unknown> {
  return JSON.parse(readFileSync(new URL(`../_api/narration/${name}.json`, import.meta.url), 'utf8')) as Record<
    string,
    unknown
  >;
}

/** Un trabajo de narración ya terminado, con su carpeta de salida (la misma `group_key` para las tomas de un texto). */
export function take(id: number, model: string, kind = 'narration'): Record<string, unknown> {
  return {
    id,
    kind,
    resource: 'gpu',
    status: 'done',
    position: id,
    params: { model, style: 'expert', voice: 'yesid', language: 'es', text: 'Hola, mundo.' },
    output_dir: `D:/out/narration/2026-11-19-${id}-hola`,
    result: null,
    error_code: null,
    error_detail: null,
    progress: 1,
    stage: null,
    created_at: '2026-11-19T10:00:00',
    started_at: null,
    finished_at: null,
    owner_pid: null,
    starred: false,
    group_key: 'narration:abc',
  };
}

export interface NarrationState {
  /** Los trabajos que la API devuelve en `GET /jobs`. Cambian con los POST y el star. */
  jobs: Record<string, unknown>[];
  /** Si true, cada trabajo encolado termina enseguida como toma (para la prueba de generar). */
  finishOnEnqueue?: boolean;
}

/** Las respuestas de Narración: el catálogo, el linter, los trabajos del estado y las tomas grabadas. */
export function narrationReplies(state: NarrationState): Replies {
  return ({ method, path, search, body }) => {
    if (method === 'GET' && path === '/catalog/narration') return fixture('catalog');
    if (method === 'POST' && path === '/narration/lint') return fixture('lint');
    if (method === 'GET' && path === '/jobs') {
      const group = new URLSearchParams(search).get('group_key');
      return group ? state.jobs.filter((job) => job.group_key === group) : state.jobs;
    }
    if (method === 'POST' && path === '/jobs') {
      const id = Math.max(2, ...state.jobs.map((job) => Number(job.id))) + 1;
      const params = (body as { params?: { model?: string } }).params;
      if (state.finishOnEnqueue) state.jobs.push(take(id, params?.model ?? 'voxcpm2'));
      return { id };
    }
    const star = /^\/jobs\/(\d+)\/star$/.exec(path);
    if (method === 'POST' && star) {
      const id = Number(star[1]);
      const group = state.jobs.find((job) => job.id === id)?.group_key;
      state.jobs = state.jobs.map((job) => (job.group_key === group ? { ...job, starred: job.id === id } : job));
      return state.jobs.find((job) => job.id === id);
    }
    if (method === 'GET' && path === '/media/info') return fixture('info');
    if (method === 'GET' && path === '/media/peaks') return fixture('peaks');
    if (method === 'GET' && path === '/files') {
      const file = new URLSearchParams(search).get('path') ?? '';
      if (file.endsWith('.wav')) return { contentType: 'audio/wav', body: silentWav(1) } satisfies Binary;
      return file.endsWith('script.json') ? fixture('script') : fixture('take');
    }
    return undefined;
  };
}

/** Abre la sección Narración desde la barra lateral y espera su título. */
export async function goToNarration(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Narración' }).click();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Narración', level: 2 })).toBeVisible();
}

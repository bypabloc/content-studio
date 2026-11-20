import { expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import type { Replies } from './app';

function fixture(name: string): unknown {
  return JSON.parse(readFileSync(new URL(`../_api/music/${name}.json`, import.meta.url), 'utf8')) as unknown;
}

/** Lo que la prueba necesita de la API: si el trabajo terminó, qué pista está elegida y cuánto dura la narración. */
export interface MusicState {
  finished: boolean;
  chosen: string | null;
  narrationSeconds?: number;
}

/** El trabajo de música del pedido, con el id y la carpeta que usan las respuestas grabadas. */
function job(state: MusicState) {
  return {
    id: 9,
    kind: 'music',
    status: state.finished ? 'done' : 'queued',
    params: {},
    output_dir: 'C:/fake/out/music/9',
    starred: false,
    group_key: 'music:e2e',
  };
}

/** Responde la sección Música desde `_api/music/` y guarda la elección que hace la prueba. */
export function musicReplies(state: MusicState): Replies {
  return ({ method, path, search, body }) => {
    if (method === 'GET' && path === '/music/styles') return fixture('styles');
    if (method === 'GET' && path === '/jobs' && search.includes('group_key=')) return state.finished ? [job(state)] : [];
    if (method === 'GET' && path === '/jobs' && search.includes('kind=narration')) return fixture('narrations');
    if (method === 'POST' && path === '/jobs') return job(state);
    if (method === 'POST' && /^\/jobs\/\d+\/choose$/.test(path)) {
      state.chosen = (body as { file: string }).file;
      return { ...(fixture('tracks') as object), chosen: state.chosen };
    }
    if (method === 'GET' && path === '/files' && search.includes('tracks.json')) {
      return { ...(fixture('tracks') as object), chosen: state.chosen };
    }
    if (method === 'GET' && path === '/files' && search.includes('script.json')) return { wav: 'narration.wav' };
    if (method === 'GET' && path === '/media/info') return { duration: state.narrationSeconds ?? 47.3, lufs: -16, true_peak: -1 };
    if (method === 'GET' && path === '/media/peaks') return { peaks: [] };
    return undefined;
  };
}

/** Lleva a la sección Música desde la barra lateral. */
export async function goToMusic(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Música' }).click();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Música', level: 2 })).toBeVisible();
}

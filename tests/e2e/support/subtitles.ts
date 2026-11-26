import { expect, type Page } from '@playwright/test';
import { apiFixture, type Call, type Failed, type Replies } from './app';

/** Un proyecto de subtítulos como lo lista `GET /subtitles` (el id 7 tiene el documento de `_api/subtitles/doc`). */
export const PROJECT = { id: 7, name: 'charla', source_path: 'C:/fake/in/charla.mp4', updated_at: '2026-11-22T10:00:00' };

/**
 * Las respuestas de la sección Subtítulos: la lista de proyectos, el documento del proyecto 7 y la exportación. Con
 * `reject`, el envío de trabajos devuelve ese error del server (el mismo código que valida `subtitles_create` y `burn`).
 */
export function subtitleReplies(
  options: { projects?: unknown[]; reject?: Failed['failed']; doc?: string; engines?: string } = {},
): Replies {
  return ({ method, path, body }) => {
    if (method === 'GET' && path === '/subtitles') return options.projects ?? [];
    if (method === 'GET' && path === '/subtitles/7') return apiFixture(options.doc ?? 'subtitles/doc');
    if (method === 'GET' && path === '/engines' && options.engines) return apiFixture(options.engines);
    if (method === 'PUT' && path === '/subtitles/7') return body;
    if (method === 'POST' && path === '/subtitles/7/export') {
      return { path: `C:/fake/out/subtitles/7-charla.${(body as { format: string }).format}` };
    }
    if (method === 'POST' && path === '/jobs' && options.reject) return { failed: options.reject } satisfies Failed;
    return undefined;
  };
}

/** Lleva a la sección Subtítulos desde la barra lateral. */
export async function goToSubtitles(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Subtítulos' }).click();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Subtítulos', level: 2 })).toBeVisible();
}

/** Los cuerpos de los envíos a `POST /jobs`, en orden: lo que la prueba comprueba del origen y del trabajo. */
export function jobBodies(calls: Call[]): unknown[] {
  return calls.filter((call) => call.method === 'POST' && call.path === '/jobs').map((call) => call.body);
}

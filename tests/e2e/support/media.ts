import { expect, type Page } from '@playwright/test';
import { apiFixture, setDialogPick, type Binary, type Failed, type Replies } from './app';

/** Un trabajo como lo devuelve la API: lo que la tabla y el A/B miran. */
export interface MediaJob {
  id: number;
  kind: string;
  status: string;
  progress: number;
  stage: string | null;
  output_dir: string;
  params: Record<string, unknown>;
  error_code: string | null;
  error_detail: string | null;
}

/** Lo que la prueba necesita de Convertir y Normalizar: los trabajos encolados, en el orden en que se pidieron. */
export interface MediaState {
  jobs: MediaJob[];
  nextId: number;
}

export function newMediaState(): MediaState {
  return { jobs: [], nextId: 1 };
}

/** Un cuadro de 1 × 1 px: el de la vista previa del encuadre, para que la imagen cargue. */
const FRAME = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
  'base64',
);

/** El cuerpo de un `POST /jobs` de medios, tal como lo manda la pantalla. */
export interface MediaBody {
  kind: string;
  params: Record<string, unknown>;
}

/**
 * Responde Convertir y Normalizar desde el estado de la prueba: el catálogo (grabado del server), la info de un video,
 * el cuadro del encuadre, la cola de medios y el reporte de sonoridad. Un trabajo nuevo queda en la cola (Convertir)
 * o listo (Normalizar, para que el A/B y la tabla tengan datos). Con `reject`, el envío devuelve ese error del server.
 */
export function mediaReplies(
  state: MediaState,
  reject?: (body: MediaBody) => Failed['failed'] | undefined,
): Replies {
  return ({ method, path, search, body }) => {
    if (method === 'GET' && path === '/catalog/media') return apiFixture('media/catalog');
    if (method === 'GET' && path === '/media/info') return apiFixture('media/info-video');
    if (method === 'GET' && path === '/media/frame') return { contentType: 'image/png', body: FRAME } satisfies Binary;
    if (method === 'GET' && path === '/jobs') {
      const kind = new URLSearchParams(search).get('kind');
      return state.jobs.filter((job) => job.kind === kind);
    }
    if (method === 'GET' && path === '/files' && search.includes('result.json')) return apiFixture('media/normalize-report');
    if (method === 'POST' && path === '/jobs' && (body as { kind?: string } | null)?.kind?.startsWith('media.')) {
      const request = body as MediaBody;
      const failed = reject?.(request);
      if (failed) return { failed };
      const id = state.nextId++;
      const folder = request.kind.replace('media.', '');
      const job: MediaJob = {
        id,
        kind: request.kind,
        status: request.kind === 'media.normalize' ? 'done' : 'queued',
        progress: request.kind === 'media.normalize' ? 1 : 0,
        stage: null,
        output_dir: `C:/fake/out/${folder}/${id}`,
        params: request.params,
        error_code: null,
        error_detail: null,
      };
      state.jobs.push(job);
      return job;
    }
    return undefined;
  };
}

/** Lleva a una sección de la barra lateral, por su nombre visible. */
export async function goToSection(page: Page, name: 'Convertir' | 'Normalizar'): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name }).click();
}

/** Elige archivos con el diálogo de la app, como lo hace «Elegir archivos» en Convertir y Normalizar. */
export async function chooseFiles(page: Page, paths: string[]): Promise<void> {
  await setDialogPick(page, paths);
  await page.getByRole('button', { name: 'Elegir archivos' }).click();
  await expect(page.getByText(paths[paths.length - 1].split('/').pop() ?? '')).toBeVisible();
}

/** Los cuerpos de los `POST /jobs` de medios que hizo la app, en orden. */
export function mediaBodies(calls: { method: string; path: string; body: unknown }[]): MediaBody[] {
  return calls
    .filter((call) => call.method === 'POST' && call.path === '/jobs')
    .map((call) => call.body as MediaBody)
    .filter((body) => body?.kind?.startsWith('media.'));
}

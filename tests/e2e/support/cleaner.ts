import { expect, type Page } from '@playwright/test';
import { apiFixture, setDialogPick, type Failed, type Replies } from './app';

/** Un trabajo como lo devuelve la API: lo que el lote y la revisión miran. */
interface Job {
  id: number;
  kind: string;
  status: string;
  progress: number;
  stage: string | null;
  output_dir: string;
  params: Record<string, unknown>;
}

/** Lo que la prueba necesita del limpiador: los análisis, los renders, los cortes guardados y los renders pedidos. */
export interface CleanState {
  analyses: Job[];
  renders: Job[];
  saved: unknown[];
  rendered: number[];
  nextId: number;
}

export function newCleanState(): CleanState {
  return { analyses: [], renders: [], saved: [], rendered: [], nextId: 9 };
}

function job(state: CleanState, kind: string, params: Record<string, unknown>): Job {
  const id = state.nextId++;
  return { id, kind, status: 'done', progress: 1, stage: null, output_dir: `C:/fake/out/clean/${id}`, params };
}

/** El análisis de un trabajo de la URL (`/clean/<id>...`): su carpeta de salida y su entrada, para la revisión. */
function analysisOf(state: CleanState, path: string): Job | undefined {
  const id = Number(path.split('/')[2]);
  return state.analyses.find((analysis) => analysis.id === id);
}

/** El documento de cortes del análisis: el fixture, con la entrada del trabajo que se revisa. */
function document(state: CleanState, path: string): Record<string, unknown> {
  const doc = apiFixture<{ params: Record<string, unknown> }>('clean/analysis');
  const found = analysisOf(state, path);
  return { ...doc, params: { ...doc.params, input: found?.params.input ?? doc.params.input } };
}

/**
 * Responde el limpiador desde el estado de la prueba: el lote (`/jobs`), el análisis (`/clean/<id>`), la transcripción
 * (`/files`) y la forma de onda. El análisis con «auto_render» también encola su render, como lo hace el server. Con
 * `reject`, el envío de un análisis devuelve ese error en vez de encolarlo.
 */
export function cleanReplies(state: CleanState, reject?: Failed['failed']): Replies {
  return ({ method, path, search, body }) => {
    if (method === 'GET' && path === '/jobs' && search.includes('kind=clean.analyze')) return state.analyses;
    if (method === 'GET' && path === '/jobs' && search.includes('kind=clean.render')) return state.renders;
    if (method === 'POST' && path === '/jobs' && (body as { kind?: string }).kind === 'clean.analyze') {
      if (reject) return { failed: reject } satisfies Failed;
      const params = (body as { params: Record<string, unknown> }).params;
      const analysis = job(state, 'clean.analyze', params);
      state.analyses.push(analysis);
      if (params.auto_render === true) state.renders.push(job(state, 'clean.render', { analysis: analysis.output_dir }));
      return analysis;
    }
    if (method === 'GET' && /^\/clean\/\d+$/.test(path)) return document(state, path);
    if (method === 'POST' && /^\/clean\/\d+\/plan$/.test(path)) return document(state, path);
    if (method === 'PUT' && /^\/clean\/\d+\/cuts$/.test(path)) {
      state.saved.push(body);
      return undefined;
    }
    if (method === 'POST' && /^\/clean\/\d+\/render$/.test(path)) {
      const analysis = analysisOf(state, path);
      state.rendered.push(Number(path.split('/')[2]));
      const render = job(state, 'clean.render', { analysis: analysis?.output_dir ?? '' });
      state.renders.push(render);
      return render;
    }
    if (method === 'GET' && path === '/files' && search.includes('transcript')) return apiFixture('clean/transcript');
    if (method === 'GET' && path === '/media/peaks') return { peaks: [] };
    return undefined;
  };
}

/** Lleva a la sección Limpiador desde la barra lateral. */
export async function goToCleaner(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Limpiador' }).click();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Limpiador', level: 2 })).toBeVisible();
}

/** Elige archivos con el diálogo de la app, como lo hace «Elegir archivos». */
export async function chooseFiles(page: Page, paths: string[]): Promise<void> {
  await setDialogPick(page, paths);
  await page.getByRole('button', { name: 'Elegir archivos' }).click();
  await expect(page.getByText(paths[paths.length - 1].split('/').pop() ?? '')).toBeVisible();
}

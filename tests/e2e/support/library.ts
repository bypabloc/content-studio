import { expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import type { Call, Replies } from './app';

function fixture<T>(name: string): T {
  return JSON.parse(readFileSync(new URL(`../_api/library/${name}.json`, import.meta.url), 'utf8')) as T;
}

interface Item {
  id: number;
  path: string;
  name: string;
  kind: string;
  job_id: number | null;
  tags: string[];
}

/** Lo que la Biblioteca guarda en la prueba: ítems con sus etiquetas, proyectos y respuestas de error por ruta. */
export interface LibraryState {
  items: Item[];
  projects: { id: number; name: string; count: number; items: number[] }[];
  failures: Record<string, { status: number; body: unknown }>;
}

export function libraryState(): LibraryState {
  return { items: fixture<{ items: Item[] }>('items').items, projects: [], failures: {} };
}

/** Los cuerpos de las llamadas a un endpoint, en orden. */
export function bodies(calls: Call[], path: string, method: string): unknown[] {
  return calls.filter((call) => call.method === method && call.path === path).map((call) => call.body);
}

/**
 * Responde la Biblioteca desde `_api/library/`: la lista (filtrada por etiqueta y proyecto como el server), el detalle,
 * las etiquetas, los proyectos, el espacio y las acciones. `state.failures` fuerza un error en una ruta.
 */
export function libraryReplies(state: LibraryState): Replies {
  const jobs = fixture<Record<string, unknown>>('jobs');
  return ({ method, path, search, body }) => {
    const failure = state.failures[`${method} ${path}`];
    if (failure) return { failed: failure };
    if (method === 'GET' && path === '/library') {
      const query = new URLSearchParams(search);
      const tag = query.get('tag');
      const project = state.projects.find((p) => String(p.id) === query.get('project'));
      const items = state.items.filter((item) => (!tag || item.tags.includes(tag)) && (!project || project.items.includes(item.id)));
      return { items, total: items.length };
    }
    if (method === 'GET' && path === '/library/folders') return [{ id: 1, path: 'D:/videos', name: 'videos' }];
    if (method === 'GET' && path === '/library/storage') return fixture('storage');
    if (method === 'POST' && path === '/library/scan') return { id: 50, kind: 'library.scan', status: 'queued', params: {} };
    if (method === 'GET' && path === '/jobs/50') return { id: 50, status: 'done' };
    if (method === 'POST' && path === '/library/trash') return { removed: (body as { items: number[] }).items.length };
    if (method === 'GET' && path === '/tags') {
      const names = [...new Set(state.items.flatMap((item) => item.tags))];
      return names.map((name) => ({ name, count: state.items.filter((item) => item.tags.includes(name)).length }));
    }
    if (method === 'GET' && path === '/projects') return state.projects.map(({ id, name, count }) => ({ id, name, count }));
    if (method === 'POST' && path === '/projects') {
      const project = { id: state.projects.length + 1, name: (body as { name: string }).name, count: 0, items: [] as number[] };
      state.projects.push(project);
      return { id: project.id, name: project.name, count: 0 };
    }
    const added = /^\/projects\/(\d+)\/items$/.exec(path);
    if (method === 'POST' && added) {
      const project = state.projects.find((p) => String(p.id) === added[1]);
      project?.items.push(...(body as { items: number[] }).items);
      if (project) project.count = project.items.length;
      return {};
    }
    const tagged = /^\/library\/(\d+)\/tags$/.exec(path);
    if (method === 'POST' && tagged) {
      const item = state.items.find((i) => String(i.id) === tagged[1]);
      item?.tags.push((body as { name: string }).name);
      return item?.tags ?? [];
    }
    const detail = /^\/library\/(\d+)$/.exec(path);
    if (method === 'GET' && detail) {
      const item = state.items.find((i) => String(i.id) === detail[1]);
      const job = item?.job_id ? (jobs[String(item.job_id)] ?? null) : null;
      return { item, job, outputs: [], takes: [] };
    }
    if (method === 'GET' && /^\/jobs\/\d+$/.test(path)) return jobs[path.split('/')[2]] ?? {};
    if (method === 'GET' && path === '/media/peaks') return { peaks: [0.2, 0.6, 0.4] };
    if (method === 'GET' && path === '/settings/library.last_scan') return { key: 'library.last_scan', value: new Date().toISOString() };
    if (/^\/library\/\d+\/(rename|move|delete)$/.test(path)) return { removed: 1 };
    return undefined;
  };
}

/** Abre la Biblioteca desde la barra lateral y espera su panel. */
export async function goToLibrary(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Biblioteca' }).click();
  await expect(page.getByRole('navigation', { name: 'Secciones de la biblioteca' })).toBeVisible();
}

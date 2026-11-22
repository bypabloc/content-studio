import { expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { type Call, type Replies, setDialogPick } from './app';

function fixture(name: string): unknown {
  return JSON.parse(readFileSync(new URL(`../_api/mix/${name}.json`, import.meta.url), 'utf8')) as unknown;
}

/** Lo que la prueba necesita de Mezcla: los trabajos de render que la API va devolviendo. */
export interface MixState {
  renders: { id: number; status: string; error_code: string | null; params: { mix_id: number } }[];
  /** Estado y código con que termina el render que la prueba encola (por defecto, en cola). */
  renderStatus?: string;
  renderError?: string | null;
}

/** Los cuerpos de las llamadas a un endpoint, en orden: lo que la prueba comprueba que la app mandó. */
export function bodies(calls: Call[], path: string, method: string): unknown[] {
  return calls.filter((call) => call.method === method && call.path === path).map((call) => call.body);
}

/**
 * Responde Mezcla desde `_api/mix/`: el proyecto (7), su curva, los guardados (PUT) y el render. Un render que se
 * encola aparece en la lista de trabajos con el estado que la prueba le dé (`state.renders`).
 */
export function mixReplies(state: MixState): Replies {
  return ({ method, path, search, body }) => {
    if (method === 'POST' && path === '/mix/prepare') return fixture('project');
    if (method === 'GET' && path === '/mix/7') return fixture('project');
    if (method === 'GET' && path === '/mix/7/curve') return fixture('curve');
    if (method === 'PUT' && path === '/mix/7') return { ...(fixture('project') as object), ...(body as object) };
    if (method === 'GET' && path === '/jobs' && search.includes('kind=mix.render')) return state.renders;
    if (method === 'GET' && path === '/jobs' && search.includes('status=done')) return [];
    if (method === 'POST' && path === '/jobs' && (body as { kind?: string }).kind === 'mix.render') {
      state.renders = state.renders.concat({ id: 9, status: state.renderStatus ?? 'queued', error_code: state.renderError ?? null, params: { mix_id: 7 } });
      return { id: 9, kind: 'mix.render', status: 'queued', params: { mix_id: 7 } };
    }
    return undefined;
  };
}

/** Abre Mezcla desde la barra lateral (grupo Editar) y espera la ranura de la voz. */
export async function goToMix(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Mezcla' }).click();
  await expect(page.getByRole('group', { name: 'Voz', exact: true })).toBeVisible();
}

/** Elige la voz y la música con el diálogo de archivos y crea el proyecto; espera el editor. */
export async function createProject(page: Page): Promise<void> {
  await setDialogPick(page, ['D:/media/voz.wav']);
  await page.getByRole('group', { name: 'Voz', exact: true }).getByRole('button', { name: 'Archivo…' }).click();
  await setDialogPick(page, ['D:/media/musica.wav']);
  await page.getByRole('group', { name: 'Música', exact: true }).getByRole('button', { name: 'Archivo…' }).click();
  await page.getByRole('button', { name: 'Crear proyecto' }).click();
  await expect(page.getByRole('button', { name: 'Región 1' })).toBeVisible();
}

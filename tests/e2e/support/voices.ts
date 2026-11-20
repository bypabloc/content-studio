import { readFileSync } from 'node:fs';
import { expect, type Page } from '@playwright/test';
import type { Call, Replies } from './app';
import { narrationReplies } from './narration';

/** Una respuesta grabada de Mis voces o del catálogo (`_api/voices/<nombre>.json`). */
function fixture(name: string): unknown {
  return JSON.parse(readFileSync(new URL(`../_api/voices/${name}.json`, import.meta.url), 'utf8')) as unknown;
}

/** El catálogo de narración con otras voces: la lista del selector de voz sale de aquí (spec 010, AC-9). */
export function narrationCatalogWith(voices: string[]): unknown {
  const catalog = JSON.parse(readFileSync(new URL('../_api/narration/catalog.json', import.meta.url), 'utf8')) as Record<
    string,
    unknown
  >;
  return { ...catalog, voices: voices.map((id) => ({ id, language: 'es' })) };
}

/** Lo que cambia durante una prueba: las tomas de «neutral» de Ana, que suben y aparecen en su lista. */
export interface VoicesState {
  takes: number[];
}

export function newVoicesState(): VoicesState {
  return { takes: [] };
}

/**
 * Responde Mis voces, la ficha de Ana, el asistente de grabación, el formulario de importar y el catálogo. Lo que no es de
 * voces (la onda, el reproductor y los archivos de audio) lo responde `narrationReplies`, para que una toma suene de verdad.
 */
export function voicesReplies(state: VoicesState): Replies {
  const media = narrationReplies({ jobs: [] });
  return (call: Call) => {
    const { method, path, body } = call;
    if (method === 'GET' && path === '/voices/profiles') return fixture('profiles');
    if (method === 'GET' && path === '/voices/profiles/ana') return fixture('profile-ana');
    if (method === 'GET' && path === '/voices/kit') return fixture('kit');
    if (method === 'GET' && path === '/voices/catalog') return fixture('catalog');
    if (method === 'GET' && path === '/voices/profiles/ana/takes/neutral') return { style: 'neutral', takes: [...state.takes] };
    if (method === 'GET' && path === '/voices/profiles/ana/takes/neutral/1') return fixture('take-1');
    if (method === 'POST' && path === '/voices/profiles/ana/takes/neutral') {
      state.takes.push(1);
      return { style: 'neutral', take: 1, job: 1 };
    }
    if (method === 'POST' && path === '/voices/profiles/ana/import') {
      state.takes.push(1);
      return { style: 'neutral', take: 1, job: 2 };
    }
    if (method === 'POST' && path === '/jobs' && (body as { kind?: string } | null)?.kind === 'voice.build') return { id: 9 };
    return media(call);
  };
}

/** Abre Mis voces desde la barra lateral y espera su título. */
export async function goToVoices(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Mis voces' }).click();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Mis voces', level: 2 })).toBeVisible();
}

/** Abre el catálogo desde la barra lateral y espera su título. */
export async function goToCatalog(page: Page): Promise<void> {
  await page.getByRole('navigation').getByRole('link', { name: 'Catálogo' }).click();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Catálogo', level: 2 })).toBeVisible();
}

/** Abre la ficha de Ana desde su tarjeta en Mis voces. */
export async function openAna(page: Page): Promise<void> {
  await goToVoices(page);
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Grabar', exact: true })).toBeVisible();
}

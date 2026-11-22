import { appendFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { chromium, expect, test as base, type Page } from '@playwright/test';
import { readOnlyApi } from './support/readonly';

// Lo que `python -m devtools app-check run` deja en el entorno (spec 024, D-7).
export const RUN = process.env.APP_CHECK_RUN ?? '';
export const DATA = process.env.APP_CHECK_DATA === 'real' ? 'real' : 'temp';
const CDP = process.env.APP_CHECK_CDP ?? '';

export interface Problems {
  console: string[];
  http: string[];
}

// La consola repite cada respuesta fallida («Failed to load resource»); esas se miran por su respuesta, con la URL.
const RESOURCE = /^Failed to load resource/;

/** Captura de la ventana real en `<run>/shots/<nombre>.png`. */
export type Shot = (name: string) => Promise<void>;

/** Tema visual sin escribir `ui.theme`: la clase `dark` de `<html>`, la misma que pone useTheme. */
export async function setTheme(page: Page, theme: 'light' | 'dark'): Promise<void> {
  await page.evaluate((dark) => document.documentElement.classList.toggle('dark', dark), theme === 'dark');
}

/**
 * La página de la ventana de Tauri por CDP. Junta errores de consola, excepciones y respuestas 5xx, que hacen fallar la
 * prueba, y en `--data=real` aborta las escrituras a la API. Cada prueba suma su resultado a `<run>/tests.jsonl`.
 */
export const test = base.extend<{ app: Page; shot: Shot }>({
  // eslint-disable-next-line no-empty-pattern -- Playwright exige el patrón de objeto aunque no use otras fixtures.
  app: async ({}, use, testInfo) => {
    if (!CDP) throw new Error('APP_CHECK_CDP is missing: run python -m devtools app-check run');
    const browser = await chromium.connectOverCDP(CDP);
    const page = browser.contexts()[0].pages()[0];
    const problems: Problems = { console: [], http: [] };
    page.on('console', (message) => {
      if (message.type() === 'error' && !RESOURCE.test(message.text())) problems.console.push(message.text());
    });
    page.on('pageerror', (error) => problems.console.push(error.message));
    // Un 5xx hace fallar la prueba; un 4xx queda en el informe (puede ser un recurso opcional que falta).
    const notFound: string[] = [];
    page.on('response', (response) => {
      const line = `${response.status()} ${response.request().method()} ${response.url()}`;
      if (response.status() >= 500) problems.http.push(line);
      else if (response.status() >= 400) notFound.push(line);
    });
    const blocked = DATA === 'real' ? await readOnlyApi(page) : [];
    // La ventana arranca con el server: la barra lateral aparece cuando get_connection respondió.
    await expect(page.getByRole('link', { name: 'Ajustes' })).toBeVisible({ timeout: 60_000 });
    await use(page);
    await page.unrouteAll({ behavior: 'ignoreErrors' });
    const record = {
      title: testInfo.title,
      status: testInfo.status,
      duration: testInfo.duration,
      problems,
      blocked_writes: blocked,
      http_4xx: [...new Set(notFound)],
    };
    if (RUN) appendFileSync(join(RUN, 'tests.jsonl'), `${JSON.stringify(record)}\n`);
    // close() de una conexión CDP solo desconecta: la ventana la cierra el Job de devtools.
    await browser.close();
    expect(problems, 'console errors, page errors or 5xx from the API').toEqual({ console: [], http: [] });
  },
  shot: async ({ app }, use) => {
    const dir = join(RUN || 'tmp/app-check', 'shots');
    mkdirSync(dir, { recursive: true });
    await use(async (name) => {
      await app.screenshot({ path: join(dir, `${name}.png`) });
    });
  },
});

export { expect };

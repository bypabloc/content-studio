import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { chromium, expect, test } from '@playwright/test';

// La app instalada (spec 022, AC-7), con `app-check run --scenario=installed --binary=<exe>`: el primer arranque muestra
// la preparación (Python, el venv y los datos) y luego la ventana; Ajustes > Acerca de muestra la versión. Sin la
// fixture: esa espera 60 s a la barra lateral, y la preparación tarda varios minutos la primera vez.
const CDP = process.env.APP_CHECK_CDP ?? '';
const SHOTS = join(process.env.APP_CHECK_RUN ?? '.', 'shots');
const PREPARE = 15 * 60_000;

test('installed: first start prepares the app, then the window and About', async () => {
  test.setTimeout(PREPARE + 120_000);
  mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.connectOverCDP(CDP);
  const page = browser.contexts()[0].pages()[0];
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));

  const preparing = page.getByText('Preparando Content Studio');
  // Con la carpeta de datos vacía (la de la corrida), la preparación tiene que aparecer: si no, no es la app instalada.
  await expect(preparing).toBeVisible({ timeout: 60_000 });
  await page.screenshot({ path: join(SHOTS, 'bootstrap-progress.png') });
  await expect(page.getByRole('link', { name: 'Ajustes' })).toBeVisible({ timeout: PREPARE });
  // app-check marca la bienvenida como vista (su e2e la prueba aparte): aquí basta la ventana lista.
  await page.screenshot({ path: join(SHOTS, 'app-ready.png') });

  await page.goto(page.url().replace(/#.*$/, '') + '#/settings');
  const about = page.getByText('Acerca de', { exact: true });
  await about.scrollIntoViewIfNeeded();
  await expect(about).toBeVisible();
  await page.screenshot({ path: join(SHOTS, 'settings-about.png') });

  await browser.close();
  expect(errors).toEqual([]);
});

import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { chromium, expect, test } from '@playwright/test';

// El updater de la app instalada (spec 022, AC-9), con `app-check run --scenario=updater --binary=<exe>` sobre un build
// de prueba cuyo endpoint es un `latest.json` local firmado con la misma clave. Acepta la versión nueva y espera a que
// la app reiniciada termine su preparación con esa versión (`venv/.app-version`).
const CDP = process.env.APP_CHECK_CDP ?? '';
const RUN = process.env.APP_CHECK_RUN ?? '.';
const NEXT = process.env.APP_CHECK_NEXT_VERSION ?? '0.1.1';
const UPDATE = 10 * 60_000;

function appVersion(): string {
  const marker = join(RUN, 'home', 'venv', '.app-version');
  return existsSync(marker) ? readFileSync(marker, 'utf-8').trim() : '';
}

test('updater: offers the new version, installs it and restarts', async () => {
  test.setTimeout(UPDATE + 5 * 60_000);
  const browser = await chromium.connectOverCDP(CDP);
  const page = browser.contexts()[0].pages()[0];
  await expect(page.getByRole('link', { name: 'Ajustes' })).toBeVisible({ timeout: 5 * 60_000 });
  const before = appVersion();
  expect(before).not.toBe(NEXT);

  await expect(page.getByText(`Hay una versión nueva: ${NEXT}.`)).toBeVisible({ timeout: 60_000 });
  await page.screenshot({ path: join(RUN, 'shots', 'update-offer.png') });
  await page.getByRole('button', { name: 'Actualizar y reiniciar' }).click();

  // El instalador corre en modo pasivo y vuelve a abrir la app, que prepara el venv de la versión nueva.
  await expect.poll(appVersion, { timeout: UPDATE, intervals: [2000] }).toBe(NEXT);
  await browser.close().catch(() => {});
});

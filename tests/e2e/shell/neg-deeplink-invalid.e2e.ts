import { expect, test } from '@playwright/test';
import { hasListener, openApp } from '../support/app';

import type { Page } from '@playwright/test';

/** Dispara `external-request` con el argv de un enlace, como lo haría Rust al recibir un segundo arranque (spec 031, AC-5). */
function emitExternal(page: Page, argv: string[]) {
  return page.evaluate(
    (args) => (window as unknown as { __emitEvent: (event: string, payload: unknown) => void }).__emitEvent('external-request', args),
    argv,
  );
}

// Un enlace fuera de la lista (spec 031, AC-4) avisa y no llama a la API.
test('AC-4: un enlace no válido avisa y no llama a la API', async ({ page }) => {
  const { calls } = await openApp(page);
  await expect.poll(() => hasListener(page, 'external-request')).toBe(true);
  await emitExternal(page, ['content-studio.exe', 'content-studio://engine/install?name=x']);
  await expect(page.getByText('Se ignoró un enlace de otra aplicación porque no es válido.')).toBeVisible();
  expect(calls.filter((call) => call.method !== 'GET')).toEqual([]);
});

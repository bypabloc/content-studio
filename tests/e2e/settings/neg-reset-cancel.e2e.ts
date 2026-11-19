import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

test('cancelar la confirmación de Restablecer no borra nada (AC-4)', async ({ page }) => {
  page.on('dialog', (dialog) => void dialog.dismiss());
  const { calls } = await openApp(page);
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  // La señal real es el diálogo: al cerrarlo con «Cancelar», confirm() devuelve false y el DELETE no sale.
  const dialog = page.waitForEvent('dialog');
  await page.getByRole('button', { name: 'Restablecer elecciones' }).click();
  await dialog;
  await page.evaluate(() => new Promise((done) => setTimeout(done))); // la página vuelve de confirm() antes de mirar

  expect(calls.some((call) => call.method === 'DELETE')).toBe(false);
});

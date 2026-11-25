import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';

test('Ajustes > Integraciones: muestra el server, guarda el puerto y copia el token (AC-11)', async ({ page }) => {
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  const { calls } = await openApp(page);
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await expect(page.getByText('http://127.0.0.1:9999', { exact: true })).toBeVisible();
  await page.getByLabel('Puerto (se aplica al reiniciar el servidor)').fill('41900');
  await expect.poll(() => calls.some((call) => call.method === 'PUT' && call.path === '/settings/api.port')).toBe(true);

  await page.getByRole('button', { name: 'Copiar token' }).click();
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe('tok');
});

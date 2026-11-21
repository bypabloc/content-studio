import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';

test('AC-7 y AC-8: cambiar la carpeta de motores en Almacenamiento', async ({ page }) => {
  page.on('dialog', (dialog) => void dialog.accept());
  const { calls: recorded } = await openApp(page);

  await page.evaluate(() => { location.hash = '#/settings'; });
  await expect(page.getByRole('heading', { name: 'Almacenamiento' })).toBeVisible();
  await setDialogPick(page, ['D:/Studio/engines-test']);
  await page.getByRole('button', { name: 'Cambiar carpeta de motores' }).click();

  await expect.poll(() => recorded.some((call) =>
    call.method === 'POST' && call.path === '/storage/move' &&
    JSON.stringify(call.body) === JSON.stringify({ target: 'engines', to: 'D:/Studio/engines-test' }),
  )).toBe(true);
});

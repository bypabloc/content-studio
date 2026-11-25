import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';

test('Ajustes > Integraciones: una carpeta que no existe avisa y no se registra', async ({ page }) => {
  const { calls } = await openApp(page, {
    replies: (call) => {
      if (call.method === 'GET' && call.path === '/inbox/folders') return [];
      if (call.method === 'POST' && call.path === '/inbox/folders') {
        return {
          failed: {
            status: 422,
            body: {
              code: 'inbox_path_not_found',
              params: { path: 'C:/fake/no-existe' },
              message: 'No existe la carpeta C:/fake/no-existe.',
            },
          },
        };
      }
      return undefined;
    },
  });
  await page.evaluate(() => {
    location.hash = '#/settings';
  });

  await setDialogPick(page, ['C:/fake/no-existe']);
  await page.getByRole('button', { name: 'Elegir carpeta' }).click();
  await expect(page.getByText('C:/fake/no-existe')).toBeVisible();
  await page.getByRole('button', { name: 'Agregar carpeta' }).click();

  await expect(page.getByText('No existe la carpeta C:/fake/no-existe.')).toBeVisible();
  expect(calls.filter((call) => call.method === 'POST' && call.path === '/inbox/folders')).toHaveLength(1);
});

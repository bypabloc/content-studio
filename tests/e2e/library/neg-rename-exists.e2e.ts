import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { bodies, goToLibrary, libraryReplies, libraryState } from '../support/library';

test('AC-4: renombrar sobre un nombre que ya existe avisa y no cambia nada', async ({ page }) => {
  const state = libraryState();
  state.failures['POST /library/2/rename'] = {
    status: 409,
    body: { code: 'path_exists', params: {}, message: 'Ya existe un archivo con ese nombre en el destino: elige otro.' },
  };
  const { calls } = await openApp(page, { replies: libraryReplies(state) });
  await goToLibrary(page);

  await page.getByRole('button', { name: 'Abrir track-1.wav' }).click();
  await page.getByRole('dialog', { name: 'track-1.wav' }).getByRole('button', { name: 'Renombrar' }).click();
  await page.getByRole('textbox', { name: 'Nombre nuevo' }).fill('track-2.wav');
  await page.getByRole('alertdialog').getByRole('button', { name: 'Renombrar' }).click();

  await expect(page.getByText('Ya existe un archivo con ese nombre en el destino: elige otro.')).toBeVisible();
  expect(bodies(calls, '/library/2/rename', 'POST')).toEqual([{ name: 'track-2.wav' }]);
});

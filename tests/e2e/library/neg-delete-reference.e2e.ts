import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToLibrary, libraryReplies, libraryState } from '../support/library';

test('AC-5: borrar con el archivo una referencia de voz responde protected_path y el aviso lo explica', async ({ page }) => {
  const state = libraryState();
  state.failures['POST /library/3/delete'] = {
    status: 403,
    body: { code: 'protected_path', params: {}, message: 'Las referencias de voz, las voces y los motores no se tocan desde la Biblioteca.' },
  };
  await openApp(page, { replies: libraryReplies(state) });
  await goToLibrary(page);

  await page.getByRole('button', { name: 'Abrir charla.mp4' }).click();
  await page.getByRole('dialog', { name: 'charla.mp4' }).getByRole('button', { name: 'Borrar' }).click();
  await page.getByRole('checkbox', { name: /Borrar también el archivo/ }).click();
  await page.getByRole('alertdialog').getByRole('button', { name: 'Borrar' }).click();

  await expect(page.getByText('Las referencias de voz, las voces y los motores no se tocan desde la Biblioteca.')).toBeVisible();
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { bodies, goToLibrary, libraryReplies, libraryState } from '../support/library';

test('«Tomas no elegidas» manda a la papelera solo lo elegido, con una confirmación que dice cuánto ocupa', async ({ page }) => {
  const { calls } = await openApp(page, { replies: libraryReplies(libraryState()) });
  await goToLibrary(page);

  await page.getByRole('button', { name: 'Espacio' }).click();
  const unchosen = page.getByRole('region', { name: 'Tomas no elegidas' });
  await unchosen.getByRole('checkbox', { name: /take\.wav/ }).click();
  await unchosen.getByRole('button', { name: 'Mandar a la papelera' }).click();
  await expect(page.getByText('Se mandarán 1 archivos (1000 KB) a la papelera de Windows.', { exact: false })).toBeVisible();
  await page.getByRole('alertdialog').getByRole('button', { name: 'Mandar a la papelera' }).click();

  await expect.poll(() => bodies(calls, '/library/trash', 'POST')).toEqual([{ items: [4] }]);
});

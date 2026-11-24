import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToLibrary, libraryReplies, libraryState } from '../support/library';

test('«Mandar a Limpiador» sobre un video abre el Limpiador con el archivo cargado', async ({ page }) => {
  await openApp(page, { replies: libraryReplies(libraryState()) });
  await goToLibrary(page);

  await page.getByRole('button', { name: 'Abrir charla.mp4' }).click();
  await page.getByRole('dialog', { name: 'charla.mp4' }).getByRole('button', { name: 'Mandar a Limpiador' }).click();

  await expect(page).toHaveURL(/#\/cleaner\?path=/);
  await expect(page.getByText('charla.mp4')).toBeVisible();
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToLibrary, libraryReplies, libraryState } from '../support/library';
import { pickOption } from '../support/select';

test('AC-8: etiquetar «reel 12», agregar a un proyecto y filtrar por los dos deja solo ese ítem', async ({ page }) => {
  await openApp(page, { replies: libraryReplies(libraryState()) });
  await goToLibrary(page);

  await page.getByRole('button', { name: 'Nuevo proyecto' }).click();
  await page.getByRole('textbox', { name: 'Nombre del proyecto' }).fill('Curso');
  await page.getByRole('button', { name: 'Crear' }).click();

  await page.getByRole('button', { name: 'Abrir charla.mp4' }).click();
  const dialog = page.getByRole('dialog', { name: 'charla.mp4' });
  await dialog.getByRole('textbox', { name: 'Etiqueta nueva' }).fill('reel 12');
  await dialog.getByRole('button', { name: 'Etiquetar' }).click();
  await pickOption(page, 'Agregar a un proyecto', 'Curso');
  await page.keyboard.press('Escape');

  await pickOption(page, 'Etiqueta', 'reel 12');
  await page.getByRole('button', { name: 'Curso (1)' }).click();
  await expect(page.getByText('1 archivos')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Abrir charla.mp4' })).toBeVisible();
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToLibrary, libraryReplies, libraryState } from '../support/library';

test('la Biblioteca muestra lo generado y lo vigilado, y el detalle reproduce el audio con su origen', async ({ page }) => {
  await openApp(page, { replies: libraryReplies(libraryState()) });
  await goToLibrary(page);

  await expect(page.getByText('4 archivos')).toBeVisible();
  await expect(page.getByRole('img', { name: 'Vista previa de charla.mp4' })).toBeVisible();
  await page.getByRole('button', { name: 'Abrir track-1.wav' }).click();

  const dialog = page.getByRole('dialog', { name: 'track-1.wav' });
  await expect(dialog.getByRole('button', { name: /reproducir/i }).first()).toBeVisible();
  await expect(dialog.getByText('D:/out/music/2026-11-20-2-lofi/track-1.wav')).toBeVisible();
  await expect(dialog.getByText('lofi-chill', { exact: false })).toBeVisible();

  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Ver en lista' }).click();
  await expect(page.getByRole('list', { name: 'Archivos de la biblioteca' }).getByRole('listitem')).toHaveCount(4);
});

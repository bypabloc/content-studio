import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToMusic, musicReplies, type MusicState } from '../support/music';

test('AC-6: con HeartMuLa (máximo 240 s) una narración de 5 min muestra el error de duración máxima', async ({ page }) => {
  const state: MusicState = { finished: false, chosen: null, narrationSeconds: 300 };
  await openApp(page, { replies: musicReplies(state) });
  await goToMusic(page);

  await page.getByRole('combobox', { name: 'Motor' }).click();
  await page.getByRole('option', { name: 'heartmula' }).click();
  await page.getByRole('button', { name: 'Igualar a…' }).click();
  await page.getByRole('button', { name: /Hola, mundo/ }).click();

  await expect(page.getByText('La duración pasa el máximo del motor: 240 segundos.')).toBeVisible();
});

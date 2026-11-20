import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToMusic, musicReplies, type MusicState } from '../support/music';

test('AC-6: «Igualar a narración» de 47,3 s con cola de 2 s deja el campo en 00:49.3', async ({ page }) => {
  const state: MusicState = { finished: false, chosen: null, narrationSeconds: 47.3 };
  await openApp(page, { replies: musicReplies(state) });
  await goToMusic(page);

  await page.getByRole('button', { name: 'Igualar a…' }).click();
  await page.getByRole('button', { name: /Hola, mundo/ }).click();

  await expect(page.getByRole('textbox', { name: 'Duración' })).toHaveValue('00:49.3');
});

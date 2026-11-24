import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToLibrary, libraryReplies, libraryState } from '../support/library';
import { musicReplies } from '../support/music';

test('AC-7: «Editar y repetir» sobre una música abre Música con los mismos estilos, duración y opciones', async ({ page }) => {
  const library = libraryReplies(libraryState());
  const music = musicReplies({ finished: false, chosen: null });
  const { calls } = await openApp(page, { replies: (call) => library(call) ?? music(call) });
  await goToLibrary(page);

  await page.getByRole('button', { name: 'Abrir track-1.wav' }).click();
  await page.getByRole('dialog', { name: 'track-1.wav' }).getByRole('button', { name: 'Editar y repetir' }).click();

  await expect(page).toHaveURL(/#\/music\?from_job=2/);
  await expect(page.getByRole('textbox', { name: 'Duración' })).toHaveValue('00:45.0');
  await page.getByRole('button', { name: 'Generar' }).click();
  await expect
    .poll(() => calls.filter((call) => call.method === 'POST' && call.path === '/jobs').map((call) => call.body))
    .toContainEqual({ kind: 'music', params: expect.objectContaining({ style: ['lofi-chill'], duration: 45, variants: 2, retries: 1 }) });
});

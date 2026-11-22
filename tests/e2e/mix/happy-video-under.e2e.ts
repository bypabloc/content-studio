import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';
import { bodies, goToMix, type MixState, mixReplies } from '../support/mix';

test('AC-5: con un video, el modo «Mezclar por debajo» viaja al proyecto', async ({ page }) => {
  const mix: MixState = { renders: [] };
  const { calls } = await openApp(page, { replies: mixReplies(mix) });
  await goToMix(page);

  await setDialogPick(page, ['D:/media/voz.wav']);
  await page.getByRole('group', { name: 'Voz', exact: true }).getByRole('button', { name: 'Archivo…' }).click();
  await setDialogPick(page, ['D:/media/musica.wav']);
  await page.getByRole('group', { name: 'Música', exact: true }).getByRole('button', { name: 'Archivo…' }).click();
  await setDialogPick(page, ['D:/media/charla.mp4']);
  await page.getByRole('group', { name: 'Video (opcional)', exact: true }).getByRole('button', { name: 'Archivo…' }).click();

  await page.getByRole('combobox', { name: 'Cómo usar el video' }).click();
  await page.getByRole('option', { name: 'Mezclar por debajo de su audio' }).click();
  await page.getByRole('button', { name: 'Crear proyecto' }).click();

  await expect.poll(() => bodies(calls, '/mix/prepare', 'POST')).toContainEqual({
    voice: 'D:/media/voz.wav',
    music: 'D:/media/musica.wav',
    video: 'D:/media/charla.mp4',
    video_mode: 'under',
  });
  await expect(page.getByRole('button', { name: 'Renderizar la mezcla' })).toBeVisible();
});

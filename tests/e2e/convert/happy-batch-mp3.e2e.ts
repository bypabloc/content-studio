import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, goToSection, mediaBodies, mediaReplies, newMediaState } from '../support/media';

test('Convertir: cinco audios a MP3 con V2 encolan cinco trabajos', async ({ page }) => {
  const state = newMediaState();
  const { calls } = await openApp(page, { replies: mediaReplies(state) });
  await goToSection(page, 'Convertir');

  await chooseFiles(page, [
    'C:/fake/in/a.wav',
    'C:/fake/in/b.wav',
    'C:/fake/in/c.wav',
    'C:/fake/in/d.wav',
    'C:/fake/in/e.wav',
  ]);
  await expect(page.getByRole('combobox', { name: 'Formato de destino' })).toHaveValue(/MP3/);
  await page.getByRole('button', { name: 'Convertir', exact: true }).click();

  await expect.poll(() => mediaBodies(calls).length).toBe(5);
  expect(mediaBodies(calls)[0]).toMatchObject({ kind: 'media.convert', params: { target: 'mp3', options: { vbr: 2 } } });
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, goToSection, mediaBodies, mediaReplies, newMediaState } from '../support/media';

test('Convertir: un video a Redes con Reels y el encuadre manual manda el recorte del cuadro', async ({ page }) => {
  const state = newMediaState();
  const { calls } = await openApp(page, { replies: mediaReplies(state) });
  await goToSection(page, 'Convertir');

  await chooseFiles(page, ['C:/fake/in/charla.mp4']);
  await page.getByRole('combobox', { name: 'Formato de destino' }).click();
  await page.getByRole('option', { name: /Redes/ }).click();
  await page.getByRole('combobox', { name: 'Preset de red' }).click();
  await page.getByRole('option', { name: /Reels/ }).click();
  await page.getByRole('combobox', { name: 'Encuadre' }).click();
  await page.getByRole('option', { name: 'Manual' }).click();
  await expect(page.getByRole('group', { name: 'Encuadre del cuadro' })).toBeVisible();
  await page.getByRole('button', { name: 'Convertir', exact: true }).click();

  await expect.poll(() => mediaBodies(calls).length).toBe(1);
  const sent = mediaBodies(calls)[0];
  expect(sent).toMatchObject({
    kind: 'media.convert',
    params: { target: 'mp4-h264', options: { width: 1080, height: 1920, reframe: { mode: 'manual' } } },
  });
  // Un 16:9 a 9:16 empieza con el alto entero y el ancho de 0,3164, centrado (x = 0,3418).
  const reframe = (sent.params.options as { reframe: { x: number; w: number } }).reframe;
  expect(reframe.w).toBeCloseTo(0.3164, 3);
  expect(reframe.x).toBeCloseTo(0.3418, 3);
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, goToSection, mediaBodies, mediaReplies, newMediaState } from '../support/media';

test('Convertir: un formato sin codificador en este ffmpeg avisa cuál falta y no encola nada', async ({ page }) => {
  const state = newMediaState();
  const { calls } = await openApp(page, {
    replies: mediaReplies(state, (body) =>
      body.params.target === 'mp4-h265'
        ? {
            status: 422,
            body: {
              code: 'codec_unavailable',
              params: { codec: 'libx265' },
              message: 'Este ffmpeg no trae el codificador libx265: instala el build completo o elige otro formato.',
            },
          }
        : undefined,
    ),
  });
  await goToSection(page, 'Convertir');

  await chooseFiles(page, ['C:/fake/in/charla.mp4']);
  await page.getByRole('combobox', { name: 'Formato de destino' }).click();
  await page.getByRole('option', { name: /H\.265/ }).click();
  await page.getByRole('button', { name: 'Convertir', exact: true }).click();

  await expect(page.getByText('Este ffmpeg no trae el codificador libx265')).toBeVisible();
  expect(mediaBodies(calls)).toHaveLength(1);
  expect(state.jobs).toHaveLength(0);
});

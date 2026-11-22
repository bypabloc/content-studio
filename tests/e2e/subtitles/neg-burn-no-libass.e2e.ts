import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToSubtitles, jobBodies, PROJECT, subtitleReplies } from '../support/subtitles';

test('neg: sin libass en el ffmpeg del sistema, Quemar avisa cómo instalarlo y el trabajo no se acepta', async ({ page }) => {
  const { calls } = await openApp(page, {
    replies: subtitleReplies({
      projects: [PROJECT],
      reject: { status: 422, body: { code: 'ffmpeg_no_libass', params: {} } },
    }),
  });
  await goToSubtitles(page);
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();

  await page.getByRole('button', { name: 'Quemar subtítulos', exact: true }).click();

  await expect(
    page.getByText('Este ffmpeg no trae libass: instala el build completo (winget install Gyan.FFmpeg).'),
  ).toBeVisible();
  // El server lo rechazó: el intento queda registrado, pero no hay un trabajo aceptado.
  expect(jobBodies(calls)).toEqual([{ kind: 'subtitles.burn', params: { project_id: 7 } }]);
});

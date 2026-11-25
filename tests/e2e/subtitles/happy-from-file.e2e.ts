import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';
import { jobBodies, goToSubtitles, subtitleReplies } from '../support/subtitles';

test('Nuevo: un archivo se transcribe en un proyecto nuevo con el origen «Transcribir un archivo»', async ({ page }) => {
  const { calls } = await openApp(page, { replies: subtitleReplies() });
  await goToSubtitles(page);

  await setDialogPick(page, ['C:/fake/in/charla.wav']);
  await page.getByRole('button', { name: 'Elegir archivo', exact: true }).click();
  await expect(page.getByLabel('Archivo o ruta de entrada')).toHaveValue('C:/fake/in/charla.wav');
  await page.getByRole('button', { name: 'Crear proyecto', exact: true }).click();

  await expect
    .poll(() => jobBodies(calls))
    .toContainEqual({ kind: 'subtitles.create', params: expect.objectContaining({ origin: 'file', input: 'C:/fake/in/charla.wav' }) });
});

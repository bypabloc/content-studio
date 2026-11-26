import { expect, test } from '@playwright/test';

import { openApp } from '../support/app';
import { goToSubtitles, jobBodies, PROJECT, subtitleReplies } from '../support/subtitles';

test('con hablantes: se encola con la identificación, el editor muestra cada hablante, cambia y renombra, y el SRT sale con nombres', async ({ page }) => {
  const { calls } = await openApp(page, {
    replies: subtitleReplies({ projects: [PROJECT], doc: 'subtitles/doc-speakers', engines: 'transcription/engines' }),
  });
  await goToSubtitles(page);

  // AC-6: el trabajo lleva el modelo, el idioma y la identificación de hablantes
  await page.getByLabel('Archivo o ruta de entrada').fill('C:/fake/in/charla.wav');
  await page.getByRole('switch', { name: 'Identificar hablantes', exact: true }).click();
  await page.getByRole('button', { name: 'Crear proyecto', exact: true }).click();
  await expect
    .poll(() => jobBodies(calls))
    .toContainEqual({
      kind: 'subtitles.create',
      params: { origin: 'file', input: 'C:/fake/in/charla.wav', model: 'large-v3-turbo', language: 'auto', diarize: true },
    });

  // AC-5: abierto el proyecto, cada cue muestra su hablante con el nombre de la leyenda
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  await expect(page.getByText('Ana', { exact: true }).first()).toBeVisible();

  // AC-5: el hablante de un cue se cambia desde su selector
  await page.getByRole('combobox', { name: 'Hablante', exact: true }).first().click();
  await page.getByRole('option', { name: 'Hablante 2', exact: true }).click();

  // AC-5: renombrar en la leyenda cambia el nombre del chip
  const name = page.getByRole('textbox', { name: 'Nombre de Ana', exact: true });
  await name.fill('Ana M.');
  await name.press('Enter');
  await expect(page.getByText('Ana M.', { exact: true }).first()).toBeVisible();

  // AC-4: el documento entero se guarda con el cambio de hablante y el nombre nuevo
  await expect
    .poll(() => calls.filter((call) => call.method === 'PUT' && call.path === '/subtitles/7').at(-1)?.body)
    .toMatchObject({
      speakers: { SPEAKER_00: { name: 'Ana M.' } },
      cues: [{ speaker: 'SPEAKER_01' }, { speaker: 'SPEAKER_01' }],
    });

  // AC-4: el SRT sale con los nombres cuando se marca «Incluir nombres de hablantes»
  await page.getByRole('checkbox', { name: 'Incluir nombres de hablantes', exact: true }).check();
  await page.getByRole('button', { name: 'SRT', exact: true }).click();
  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/subtitles/7/export')?.body)
    .toEqual({ format: 'srt', speaker_labels: true });
  await expect(page.getByText('Guardado en C:/fake/out/subtitles/7-charla.srt', { exact: true })).toBeVisible();
});

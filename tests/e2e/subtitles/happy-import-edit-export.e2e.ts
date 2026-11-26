import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';
import { pickOption } from '../support/select';
import { goToSubtitles, jobBodies, PROJECT, subtitleReplies } from '../support/subtitles';

test('Importar un SRT, corregir un cue, guardarlo solo y exportar VTT', async ({ page }) => {
  const { calls } = await openApp(page, { replies: subtitleReplies({ projects: [PROJECT] }) });
  await goToSubtitles(page);

  await pickOption(page, 'Origen', 'Importar SRT o VTT');
  await setDialogPick(page, ['C:/fake/in/charla.srt']);
  await page.getByRole('button', { name: 'Elegir archivo', exact: true }).click();
  await page.getByRole('button', { name: 'Crear proyecto', exact: true }).click();
  await expect
    .poll(() => jobBodies(calls))
    .toContainEqual({ kind: 'subtitles.create', params: expect.objectContaining({ origin: 'import', input: 'C:/fake/in/charla.srt' }) });

  await page.getByRole('button', { name: 'Abrir', exact: true }).click();
  // El primer cue es el de la transcripción del documento: su campo de texto tiene la etiqueta de CueList.
  const cue = page.getByLabel('Texto del subtítulo', { exact: true }).first();
  await expect(cue).toHaveValue('hola a todos');
  await cue.fill('hola a amigos');
  // El cambio se guarda solo, con el documento entero, 1 s después del último cambio.
  await expect
    .poll(() => calls.find((call) => call.method === 'PUT' && call.path === '/subtitles/7')?.body)
    .toEqual(expect.objectContaining({ cues: expect.arrayContaining([expect.objectContaining({ text: 'hola a amigos' })]) }));

  await page.getByRole('button', { name: 'VTT', exact: true }).click();
  await expect(page.getByText('Guardado en C:/fake/out/subtitles/7-charla.vtt')).toBeVisible();
});

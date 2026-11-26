import { expect, test } from '@playwright/test';
import { openApp, setDialogPick } from '../support/app';
import { pickOption } from '../support/select';
import { goToSubtitles, jobBodies, subtitleReplies } from '../support/subtitles';

test('neg: importar un .txt se rechaza y el aviso dice qué archivo sirve', async ({ page }) => {
  const { calls } = await openApp(page, {
    replies: subtitleReplies({
      reject: { status: 422, body: { code: 'unsupported_subtitle_format', params: { input: 'C:/fake/in/notas.txt' } } },
    }),
  });
  await goToSubtitles(page);

  await pickOption(page, 'Origen', 'Importar SRT o VTT');
  await setDialogPick(page, ['C:/fake/in/notas.txt']);
  await page.getByRole('button', { name: 'Elegir archivo', exact: true }).click();
  await page.getByRole('button', { name: 'Crear proyecto', exact: true }).click();

  await expect(page.getByText('«C:/fake/in/notas.txt» no es un SRT ni un VTT. Elige un archivo .srt o .vtt.')).toBeVisible();
  expect(jobBodies(calls)).toEqual([{ kind: 'subtitles.create', params: expect.objectContaining({ origin: 'import', input: 'C:/fake/in/notas.txt' }) }]);
});

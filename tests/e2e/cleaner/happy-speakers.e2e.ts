import { expect, test } from '@playwright/test';

import { apiFixture, openApp } from '../support/app';
import { chooseFiles, cleanReplies, goToCleaner, newCleanState } from '../support/cleaner';
import { jobBodies } from '../support/subtitles';

test('con hablantes: el análisis pide diarize, la revisión colorea cada palabra con su hablante y Subtitular sale del video limpio (AC-8)', async ({
  page,
}) => {
  const state = newCleanState();
  const replies = cleanReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => (call.method === 'GET' && call.path === '/engines' ? apiFixture('transcription/engines') : replies(call)),
  });
  await goToCleaner(page);
  await chooseFiles(page, ['C:/fake/in/charla.mp4']);

  // AC-8: «Identificar hablantes» pasa diarize al análisis
  await page.getByRole('switch', { name: 'Identificar hablantes', exact: true }).click();
  await page.getByRole('button', { name: 'Analizar', exact: true }).click();
  await expect
    .poll(() => jobBodies(calls))
    .toContainEqual(expect.objectContaining({ kind: 'clean.analyze', params: expect.objectContaining({ diarize: true }) }));

  // AC-8: cada palabra lleva el color de su hablante y la leyenda muestra los nombres
  await page.getByRole('button', { name: 'Revisar', exact: true }).click();
  await expect(page.getByRole('button', { name: 'hola', exact: true })).toHaveCSS('border-bottom-color', 'rgb(37, 99, 235)');
  await expect(page.getByRole('button', { name: 'mundo', exact: true })).toHaveCSS('border-bottom-color', 'rgb(220, 38, 38)');
  await expect(page.getByText('Ana', { exact: true })).toBeVisible();

  // AC-8: Subtitular sale del video limpio del análisis (sus hablantes van con el análisis)
  await page.getByRole('button', { name: 'Renderizar', exact: true }).click();
  await page.getByRole('button', { name: 'Subtitular', exact: true }).click();
  await expect.poll(() => jobBodies(calls)).toContainEqual({
    kind: 'subtitles.create',
    params: {
      origin: 'cleaner',
      input: 'C:/fake/cache/transcription/9-transcript.json',
      analysis: 'C:/fake/out/clean/9',
      source: 'C:/fake/out/clean/10/clean.mp4',
    },
  });
});

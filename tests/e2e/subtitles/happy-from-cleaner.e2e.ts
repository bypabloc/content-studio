import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, cleanReplies, goToCleaner, newCleanState } from '../support/cleaner';
import { jobBodies } from '../support/subtitles';

test('AC-11: Subtitular sobre el resultado del Limpiador crea el proyecto con su transcript, sin encolar otra transcripción', async ({
  page,
}) => {
  const state = newCleanState();
  const { calls } = await openApp(page, { replies: cleanReplies(state) });
  await goToCleaner(page);
  await chooseFiles(page, ['C:/fake/in/charla.mp4']);
  await page.getByRole('button', { name: 'Analizar', exact: true }).click();
  await page.getByRole('button', { name: 'Revisar', exact: true }).click();

  // Sin el video limpio (sin render), el botón espera.
  await expect(page.getByRole('button', { name: 'Subtitular', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Renderizar', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Subtitular', exact: true })).toBeEnabled();
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
  // Solo el análisis que pidió la prueba y el trabajo de subtítulos: ninguna transcripción nueva en la cola.
  expect(jobBodies(calls).map((body) => (body as { kind: string }).kind)).toEqual(['clean.analyze', 'subtitles.create']);
});

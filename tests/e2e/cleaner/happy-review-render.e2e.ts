import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, cleanReplies, goToCleaner, newCleanState } from '../support/cleaner';

test('se elige un video, se analiza y se revisa: los cortes son regiones y «Renderizar» guarda los cortes y encola el render', async ({
  page,
}) => {
  const state = newCleanState();
  const { calls } = await openApp(page, { replies: cleanReplies(state) });
  await goToCleaner(page);

  await chooseFiles(page, ['C:/fake/in/charla.mp4']);
  await page.getByRole('button', { name: 'Analizar', exact: true }).click();

  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/jobs')?.body)
    .toEqual({
      kind: 'clean.analyze',
      params: expect.objectContaining({ input: 'C:/fake/in/charla.mp4', model: 'large-v3-turbo', auto_render: false }),
    });

  await page.getByRole('button', { name: 'Revisar', exact: true }).click();
  await expect(page.getByRole('button', { name: /^Corte 1:/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /^Corte 2:/ })).toBeVisible();

  await page.getByRole('button', { name: 'Renderizar', exact: true }).click();
  await expect.poll(() => calls.some((call) => call.method === 'PUT' && /^\/clean\/\d+\/cuts$/.test(call.path))).toBe(true);
  await expect.poll(() => calls.some((call) => call.method === 'POST' && /^\/clean\/\d+\/render$/.test(call.path))).toBe(true);
});

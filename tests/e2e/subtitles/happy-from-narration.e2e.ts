import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState, take } from '../support/narration';
import { jobBodies } from '../support/subtitles';

test('AC-4: Subtitular sobre una toma de narración crea el proyecto con el texto del guion', async ({
  page,
}) => {
  const state: NarrationState = { jobs: [take(3, 'voxcpm2')] };
  const { calls } = await openApp(page, { replies: narrationReplies(state) });
  await goToNarration(page);

  await page.getByRole('button', { name: 'Subtitular', exact: true }).click();

  await expect.poll(() => jobBodies(calls)).toContainEqual({
    kind: 'subtitles.create',
    params: expect.objectContaining({ origin: 'narration', script: 'Hola, mundo.', language: 'es' }),
  });
});

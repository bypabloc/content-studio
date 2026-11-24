import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { combine, llmReplies } from '../support/llm';
import { goToMusic, musicReplies, type MusicState } from '../support/music';

test('«Describir en español» llena caption, tonalidad, BPM y compás como sugerencia editable', async ({ page }) => {
  const state: MusicState = { finished: false, chosen: null };
  const { calls } = await openApp(page, { replies: combine(llmReplies(), musicReplies(state)) });
  await goToMusic(page);

  await page.getByRole('button', { name: 'Texto libre' }).click();
  await page.getByRole('textbox', { name: 'Qué música quieres, en español' }).fill('algo tranquilo con piano y lluvia para un tutorial de cocina');
  await page.getByRole('button', { name: 'Describir en español' }).click();
  await page.getByRole('button', { name: 'Usar la sugerencia' }).click();

  await expect(page.getByRole('textbox', { name: 'Descripción en inglés' })).toHaveValue(
    'soft piano, rain ambience, warm, cooking tutorial background, no vocals',
  );
  await expect(page.getByRole('button', { name: 'C Major' })).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByRole('spinbutton', { name: 'BPM' })).toHaveValue('85');
  expect(calls.find((call) => call.method === 'POST' && call.path === '/jobs')?.body).toEqual({
    kind: 'llm.music_caption',
    params: { description: 'algo tranquilo con piano y lluvia para un tutorial de cocina' },
  });
});

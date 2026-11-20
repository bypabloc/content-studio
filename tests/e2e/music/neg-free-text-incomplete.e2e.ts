import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToMusic, musicReplies, type MusicState } from '../support/music';

test('AC-7: en «Texto libre» Generar queda deshabilitado mientras falte el BPM', async ({ page }) => {
  const state: MusicState = { finished: false, chosen: null };
  const { calls } = await openApp(page, { replies: musicReplies(state) });
  await goToMusic(page);

  await page.getByRole('button', { name: 'Texto libre' }).click();
  await page.getByRole('textbox', { name: 'Descripción en inglés' }).fill('warm lofi piano');
  await page.getByRole('button', { name: 'C Major' }).click();

  await expect(page.getByRole('button', { name: 'Generar' })).toBeDisabled();
  expect(calls.some((call) => call.method === 'POST' && call.path === '/jobs')).toBe(false);
});

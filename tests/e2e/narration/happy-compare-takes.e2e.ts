import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState, take } from '../support/narration';

test('AC-10: Comparar muestra las dos tomas del texto; elegir una la marca con ★, y al reproducir una se pausa la otra', async ({
  page,
}) => {
  const state: NarrationState = { jobs: [take(3, 'voxcpm2'), take(4, 'omnivoice', 'narration.regenerate')] };
  const { calls } = await openApp(page, { replies: narrationReplies(state) });
  await goToNarration(page);

  await page.getByRole('button', { name: 'Comparar' }).click();
  const compare = page.getByRole('region', { name: 'Comparar tomas' });
  const columns = compare.getByRole('article');
  await expect(columns).toHaveCount(2);

  // Elegir la primera toma la marca con ★; la otra no cambia.
  await columns.nth(0).getByRole('button', { name: 'Elegir' }).click();
  await expect(columns.nth(0).getByText('Elegida')).toBeVisible();
  await expect(columns.nth(1).getByRole('button', { name: 'Elegir' })).toBeVisible();
  expect(calls.some((call) => call.method === 'POST' && call.path === '/jobs/3/star')).toBe(true);

  // Reproducir la segunda; al reproducir la primera, la segunda se pausa.
  await columns.nth(1).getByRole('button', { name: 'Reproducir' }).click();
  await expect(columns.nth(1).getByRole('button', { name: 'Pausar' })).toBeVisible();
  await columns.nth(0).getByRole('button', { name: 'Reproducir' }).click();
  await expect(columns.nth(0).getByRole('button', { name: 'Pausar' })).toBeVisible();
  await expect(columns.nth(1).getByRole('button', { name: 'Reproducir' })).toBeVisible();
});

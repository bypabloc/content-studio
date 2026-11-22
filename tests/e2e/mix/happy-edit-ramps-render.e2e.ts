import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { bodies, createProject, goToMix, type MixState, mixReplies } from '../support/mix';

test('AC-6: mover una región y cambiar el ducking guarda la mezcla, y el render entra en la cola', async ({ page }) => {
  const mix: MixState = { renders: [] };
  const { calls } = await openApp(page, { replies: mixReplies(mix) });
  await goToMix(page);
  await createProject(page);

  await page.getByRole('button', { name: 'Región 1' }).press('ArrowRight');
  await expect.poll(() => bodies(calls, '/mix/7', 'PUT')).toContainEqual({ regions: [[0.9, 2.5]], params: {} });

  await page.getByRole('combobox', { name: 'Bajar la música (dB)' }).click();
  await page.getByRole('option', { name: '-9' }).click();
  await expect.poll(() => bodies(calls, '/mix/7', 'PUT')).toContainEqual({ regions: [[0.8, 2.4]], params: { duck_db: -9 } });

  await page.getByRole('button', { name: 'Renderizar la mezcla' }).click();
  await expect.poll(() => bodies(calls, '/jobs', 'POST')).toContainEqual({ kind: 'mix.render', params: { mix_id: 7 } });
  await expect(page.getByText('La mezcla se encoló.')).toBeVisible();
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { createProject, goToMix, type MixState, mixReplies } from '../support/mix';

test('AC-4: un render que falla con music_too_short lo dice en el editor', async ({ page }) => {
  const mix: MixState = { renders: [], renderStatus: 'failed', renderError: 'music_too_short' };
  await openApp(page, { replies: mixReplies(mix) });
  await goToMix(page);
  await createProject(page);

  await page.getByRole('button', { name: 'Renderizar la mezcla' }).click();

  await expect(page.getByRole('alert')).toContainText('La música es más corta que la mezcla', { timeout: 10_000 });
});

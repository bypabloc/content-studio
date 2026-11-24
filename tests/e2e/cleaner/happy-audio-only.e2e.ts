import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, cleanReplies, goToCleaner, newCleanState } from '../support/cleaner';

test('un audio sin video se revisa con su onda y sin reproductor de video', async ({ page }) => {
  const state = newCleanState();
  await openApp(page, { replies: cleanReplies(state) });
  await goToCleaner(page);

  await chooseFiles(page, ['C:/fake/in/nota.wav']);
  await page.getByRole('button', { name: 'Analizar', exact: true }).click();
  await page.getByRole('button', { name: 'Revisar', exact: true }).click();

  await expect(page.getByRole('button', { name: /^Corte 1:/ })).toBeVisible();
  await expect(page.locator('audio')).toHaveCount(1);
  await expect(page.locator('video')).toHaveCount(0);
});

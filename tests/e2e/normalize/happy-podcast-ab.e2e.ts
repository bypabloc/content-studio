import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { chooseFiles, goToSection, mediaBodies, mediaReplies, newMediaState } from '../support/media';

test('Normalizar: un audio con el preset podcast muestra antes y después, y el A/B escucha el normalizado', async ({ page }) => {
  const state = newMediaState();
  const { calls } = await openApp(page, { replies: mediaReplies(state) });
  await goToSection(page, 'Normalizar');

  await chooseFiles(page, ['C:/fake/in/charla.wav']);
  await expect(page.getByRole('combobox', { name: 'Sonoridad' })).toHaveValue(/Podcast/);
  await page.getByRole('button', { name: 'Normalizar', exact: true }).click();

  await expect.poll(() => mediaBodies(calls)[0]?.params.preset).toBe('podcast');
  await expect(page.getByText('-30.0')).toBeVisible();
  await expect(page.getByText('-16.0')).toBeVisible();

  await page.getByRole('button', { name: 'Escuchar', exact: true }).click();
  await page.getByRole('button', { name: 'Normalizado', exact: true }).click();
  await expect(page.locator('audio')).toHaveAttribute('src', /normalized\.wav/);
});

import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToNarration } from '../support/narration';
import { goToCatalog, narrationCatalogWith, newVoicesState, voicesReplies } from '../support/voices';

test('AC-7 y AC-9: marcar una favorita, construir una voz del catálogo y verla primera en Narración', async ({ page }) => {
  const state = newVoicesState();
  const replies = voicesReplies(state);
  // La narración necesita dos voces para que el orden de favoritas se vea en el selector.
  const { calls } = await openApp(page, {
    replies: (call) =>
      call.method === 'GET' && call.path === '/catalog/narration' ? narrationCatalogWith(['yesid', 'maria']) : replies(call),
  });
  await goToCatalog(page);

  await page.getByRole('button', { name: 'Marcar maria como favorita' }).click();
  await expect
    .poll(() => calls.find((call) => call.method === 'PUT' && call.path === '/settings/voices.favorites')?.body)
    .toEqual({ value: ['maria'] });

  await page.getByRole('button', { name: 'Construir yesid' }).click();
  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/jobs')?.body)
    .toEqual({ kind: 'voice.build', params: { voices: ['yesid'], force: false } });

  await goToNarration(page);
  await expect(page.getByRole('combobox', { name: 'Voz', exact: true })).toHaveValue('maria');
});

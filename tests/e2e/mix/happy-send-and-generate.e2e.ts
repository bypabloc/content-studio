import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState, take } from '../support/narration';
import { type MixState, mixReplies } from '../support/mix';

test('AC-7: «Mandar a Mezclar» desde una narración carga la voz, y «Generar música» iguala a su duración', async ({
  page,
}) => {
  const narration: NarrationState = { jobs: [take(3, 'voxcpm2')] };
  const mix: MixState = { renders: [] };
  await openApp(page, { replies: (call) => narrationReplies(narration)(call) ?? mixReplies(mix)(call) });
  await goToNarration(page);

  await page.getByRole('button', { name: 'Mandar a Mezclar' }).click();
  await expect(page.getByRole('group', { name: 'Voz', exact: true })).toContainText('voxcpm2-expert.wav');

  await page.getByRole('button', { name: 'Generar música para esta voz' }).click();
  await expect(page.getByRole('textbox', { name: 'Duración' })).toHaveValue('00:02.5');
});

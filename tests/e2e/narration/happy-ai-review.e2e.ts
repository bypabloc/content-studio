import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { combine, llmReplies } from '../support/llm';
import { goToNarration, narrationReplies, type NarrationState } from '../support/narration';

test('AC-9: «Revisar con IA» muestra un diff por párrafo; aceptar uno y descartar otro deja solo el aceptado', async ({ page }) => {
  const state: NarrationState = { jobs: [] };
  const { calls } = await openApp(page, { replies: combine(llmReplies(), narrationReplies(state)) });
  await goToNarration(page);

  const script = page.getByRole('textbox', { name: 'Guion' });
  await script.fill('Tienes 24 horas; es DEMO.\n\nSon 3 pasos; nada más.');
  await page.getByRole('button', { name: 'Revisar con IA' }).click();

  const review = page.getByRole('region', { name: 'Sugerencias para el guion' });
  await expect(review.getByText('Regla 13: 24 → veinticuatro')).toBeVisible();
  await review.getByRole('button', { name: 'Aceptar', exact: true }).first().click();
  await review.getByRole('button', { name: 'Descartar' }).click();

  await expect(script).toHaveValue('Tienes veinticuatro horas. Es demo.\n\nSon 3 pasos; nada más.');
  expect(calls.find((call) => call.method === 'POST' && call.path === '/jobs')?.body).toEqual({
    kind: 'llm.script_review',
    params: { text: 'Tienes 24 horas; es DEMO.\n\nSon 3 pasos; nada más.' },
  });
});

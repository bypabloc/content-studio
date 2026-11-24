import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { combine, llmReplies } from '../support/llm';
import { goToNarration, narrationReplies } from '../support/narration';

test('AC-9: con el asistente apagado en Ajustes, Narración no muestra «Revisar con IA»', async ({ page }) => {
  await openApp(page, { settings: { 'llm.enabled': false }, replies: combine(llmReplies({ enabled: false }), narrationReplies({ jobs: [] })) });
  await goToNarration(page);
  await page.getByRole('textbox', { name: 'Guion' }).fill('Tienes 24 horas.');

  await expect(page.getByRole('button', { name: 'Revisar con IA' })).toHaveCount(0);

  await page.goto('/#/settings');
  await expect(page.getByRole('checkbox', { name: 'Mostrar los botones de IA' })).not.toBeChecked();
});

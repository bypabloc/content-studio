import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState } from '../support/narration';

test('AC-8: Ctrl+Enter encola la narración con sus opciones y, al terminar, la toma muestra la onda y el LUFS', async ({
  page,
}) => {
  const state: NarrationState = { jobs: [], finishOnEnqueue: true };
  const { calls } = await openApp(page, { replies: narrationReplies(state) });
  await goToNarration(page);
  // El catálogo llega aparte: Generar no encola hasta tener motor y estilo.
  await expect(page.getByRole('combobox', { name: 'Motor' })).toHaveValue('voxcpm2');

  await page.getByRole('textbox', { name: 'Guion' }).fill('Hola, mundo.');
  await page.keyboard.press('Control+Enter');

  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/jobs')?.body)
    .toEqual({
      kind: 'narration',
      params: expect.objectContaining({ text: 'Hola, mundo.', model: 'voxcpm2', style: 'expert', language: 'es' }),
    });
  // Cuando la cola devuelve la toma terminada, la sección muestra su volumen y su reproductor.
  await expect(page.getByText('-16.2 LUFS · pico -1.4 dB')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reproducir' })).toBeVisible();
});

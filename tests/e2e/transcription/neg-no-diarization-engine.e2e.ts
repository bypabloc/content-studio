import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { transcriptionReplies } from '../support/transcription';

test('sin el motor de hablantes, el interruptor está apagado y enlaza a Motores', async ({ page }) => {
  await openApp(page, { replies: transcriptionReplies({ engines: 'transcription/engines-without-pyannote' }) });
  await page.getByRole('navigation').getByRole('link', { name: 'Transcripción' }).click();

  // AC-3: el interruptor no se puede usar y la ayuda lleva a Motores
  await expect(page.getByRole('switch', { name: 'Identificar hablantes' })).toBeDisabled();
  await expect(page.getByText('Instala el motor de diarización para identificar hablantes.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Ir a Motores' })).toHaveAttribute('href', '#/engines');
});

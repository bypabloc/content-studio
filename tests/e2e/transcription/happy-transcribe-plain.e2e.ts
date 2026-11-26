import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { transcriptionReplies } from '../support/transcription';

test('sin identificar hablantes, la transcripción es un párrafo por segmento', async ({ page }) => {
  const { calls } = await openApp(page, { replies: transcriptionReplies({ transcript: 'transcription/transcript-plain' }) });
  await page.getByRole('navigation').getByRole('link', { name: 'Transcripción' }).click();

  await page.getByRole('textbox', { name: 'Archivo' }).fill('C:/fake/in/charla.wav');
  await page.getByRole('button', { name: 'Transcribir', exact: true }).click();

  // AC-4: el trabajo va sin hablantes y el texto no muestra leyenda
  const created = calls.find((call) => call.method === 'POST' && call.path === '/jobs');
  expect(created?.body).toEqual({ kind: 'transcribe', params: expect.not.objectContaining({ diarize: true }) });
  await expect(page.getByText('hola amigo', { exact: true })).toBeVisible();
  await expect(page.getByRole('list', { name: 'Hablantes' })).toHaveCount(0);
});

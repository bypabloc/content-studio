import { expect, test } from '@playwright/test';

import { openApp } from '../support/app';
import { goToSubtitles, subtitleReplies } from '../support/subtitles';

test('sin el motor de hablantes, el interruptor está apagado y enlaza a Motores', async ({ page }) => {
  await openApp(page, { replies: subtitleReplies({ engines: 'transcription/engines-without-pyannote' }) });
  await goToSubtitles(page);

  // AC-6: el interruptor no se puede usar y la ayuda lleva a Motores
  await expect(page.getByRole('switch', { name: 'Identificar hablantes', exact: true })).toBeDisabled();
  await expect(page.getByText('Instala el motor de diarización para identificar hablantes.', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Ir a Motores', exact: true })).toHaveAttribute('href', '#/engines');
});

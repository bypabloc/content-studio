import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { pickOption } from '../support/select';
import { transcriptionReplies } from '../support/transcription';

test('una transcripción con dos hablantes muestra sus nombres, se renombra, se exporta y pasa a subtítulos', async ({ page }) => {
  const { calls } = await openApp(page, { replies: transcriptionReplies() });
  await page.getByRole('navigation').getByRole('link', { name: 'Transcripción' }).click();
  await expect(page.getByRole('main').getByRole('heading', { name: 'Transcribir un archivo', level: 2 })).toBeVisible();

  await page.getByRole('textbox', { name: 'Archivo' }).fill('C:/fake/in/charla.wav');
  await page.getByRole('switch', { name: 'Identificar hablantes' }).click();
  await pickOption(page, 'Hablantes', 'Exacto');
  await page.getByRole('spinbutton', { name: 'Número de hablantes' }).fill('2');
  await page.getByRole('button', { name: 'Transcribir', exact: true }).click();

  // AC-1, AC-2 y AC-4: el trabajo se encola con los hablantes y el texto muestra un bloque por hablante
  const created = calls.find((call) => call.method === 'POST' && call.path === '/jobs');
  expect(created?.body).toEqual({ kind: 'transcribe', params: expect.objectContaining({ input: 'C:/fake/in/charla.wav', diarize: true, num_speakers: 2 }) });
  await expect(page.getByRole('heading', { name: 'Hablante 1', level: 3 })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Hablante 2', level: 3 })).toBeVisible();
  await expect(page.getByRole('button', { name: 'mundo', exact: true })).toBeVisible();

  // AC-5: renombrar guarda el mapa entero y el texto lo muestra
  await page.getByRole('textbox', { name: 'Nombre de Hablante 1' }).fill('Ana');
  await page.getByRole('textbox', { name: 'Nombre de Hablante 1' }).press('Enter');
  await expect(page.getByRole('heading', { name: 'Ana', level: 3 })).toBeVisible();
  const saved = calls.find((call) => call.method === 'PUT' && call.path === '/jobs/7/speakers');
  expect(saved?.body).toEqual({
    SPEAKER_00: { name: 'Ana', color: '#2563eb' },
    SPEAKER_01: { name: 'Hablante 2', color: '#dc2626' },
  });

  // AC-6: el texto se exporta y la app dice dónde quedó
  await page.getByRole('button', { name: 'Exportar texto', exact: true }).click();
  await expect(page.getByText('Texto guardado en D:/out/transcript.txt')).toBeVisible();

  // AC-7: crear subtítulos abre ese proyecto
  await page.getByRole('button', { name: 'Crear subtítulos', exact: true }).click();
  await expect(page).toHaveURL(/#\/subtitles\?project=9/);
});

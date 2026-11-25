import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { pickOption } from '../support/select';
import { speakersReplies } from '../support/speakers';

test('identificar hablantes muestra la línea de tiempo, guarda un nombre y enfoca un hablante', async ({ page }) => {
  const { calls } = await openApp(page, { replies: speakersReplies() });
  await page.getByRole('navigation').getByRole('link', { name: 'Hablantes', exact: true }).click();
  await expect(page.getByText('Identificar quién habla y cuándo', { exact: true })).toBeVisible();

  await page.getByRole('textbox', { name: 'Archivo', exact: true }).fill('C:/fake/in/charla.wav');
  await pickOption(page, 'Hablantes', 'Exacto');
  await page.getByRole('spinbutton', { name: 'Número de hablantes', exact: true }).fill('2');
  await page.getByRole('button', { name: 'Identificar', exact: true }).click();

  // AC-1: el trabajo se encola con el archivo y el número exacto de hablantes
  const created = calls.find((call) => call.method === 'POST' && call.path === '/jobs');
  expect(created?.body).toEqual({ kind: 'diarize', params: { input: 'C:/fake/in/charla.wav', num_speakers: 2 } });

  // AC-2: la línea de tiempo y la leyenda muestran a los dos hablantes
  await expect(page.getByRole('group', { name: 'Línea de tiempo de hablantes', exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Nombre de Hablante 1', exact: true })).toBeVisible();

  // AC-3: renombrar guarda el mapa entero con el nombre nuevo
  await page.getByRole('textbox', { name: 'Nombre de Hablante 1', exact: true }).fill('Ana');
  await page.getByRole('textbox', { name: 'Nombre de Hablante 1', exact: true }).press('Enter');
  await expect(page.getByRole('textbox', { name: 'Nombre de Ana', exact: true })).toBeVisible();
  const saved = calls.find((call) => call.method === 'PUT' && call.path === '/jobs/7/speakers');
  expect(saved?.body).toEqual({
    SPEAKER_00: { name: 'Ana', color: '#2563eb' },
    SPEAKER_01: { name: 'Hablante 2', color: '#dc2626' },
  });

  // AC-2: enfocar un hablante deja su nombre en el selector
  await pickOption(page, 'Solo este hablante', 'Hablante 2');
  await expect(page.getByRole('combobox', { name: 'Solo este hablante', exact: true })).toHaveValue('Hablante 2');
});

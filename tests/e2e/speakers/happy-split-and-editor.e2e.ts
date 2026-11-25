import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { speakersReplies } from '../support/speakers';

test('un resultado lista sus archivos, separa un audio por hablante y abre el Editor con sus marcadores', async ({ page }) => {
  const { calls } = await openApp(page, { replies: speakersReplies() });
  await page.getByRole('navigation').getByRole('link', { name: 'Hablantes', exact: true }).click();
  await page.evaluate(() => {
    window.location.hash = '#/speakers?from_job=7';
  });
  await expect(page.getByRole('group', { name: 'Línea de tiempo de hablantes', exact: true })).toBeVisible();

  // AC-4: los archivos de turnos y la carpeta donde están
  await expect(page.getByText('turns.csv', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Abrir carpeta', exact: true })).toBeVisible();

  // AC-5: un audio por hablante, con su reproductor y su nombre
  await page.getByRole('button', { name: 'Un audio por hablante', exact: true }).click();
  const split = calls.find((call) => call.method === 'POST' && call.path === '/jobs');
  expect(split?.body).toEqual({ kind: 'diarize.split', params: { input: 'C:/fake/in/charla.wav', turns: 'D:/out/diarize-job' } });
  // Hay tres <audio>: el reproductor del archivo y uno por hablante, con su nombre
  await expect(page.getByLabel('Hablante 1', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Hablante 2', { exact: true })).toBeVisible();

  // AC-6: abrir en el Editor crea el proyecto desde el trabajo y navega a él
  await page.getByRole('button', { name: 'Abrir en el Editor', exact: true }).click();
  await expect(page).toHaveURL(/#\/editor\?project=/);
  const created = calls.find((call) => call.method === 'POST' && call.path === '/editor/projects/from-diarization');
  expect(created?.body).toEqual({ job: 7 });
});

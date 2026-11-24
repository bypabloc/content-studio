import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { goToLibrary, libraryReplies, libraryState } from '../support/library';
import { combine, llmReplies } from '../support/llm';

test('Publicar desde el detalle de un video: títulos, hashtags y capítulos de YouTube listos para copiar', async ({ page }) => {
  const { calls } = await openApp(page, { replies: combine(llmReplies(), libraryReplies(libraryState())) });
  await goToLibrary(page);
  await page.getByRole('button', { name: 'Abrir charla.mp4' }).click();

  const publish = page.getByRole('dialog').getByRole('region', { name: 'Publicar' });
  await publish.getByRole('checkbox', { name: 'TikTok' }).check();
  await publish.getByRole('button', { name: 'Generar' }).click();

  await expect(publish.getByText('Cómo crear una cita en tres pasos')).toBeVisible();
  await expect(publish.getByText('#agenda #clinica')).toBeVisible();
  await expect(publish.getByText(/0:00 Inicio/)).toBeVisible();
  const body = calls.find((call) => call.method === 'POST' && call.path === '/jobs')?.body as { kind: string; params: { platforms: string[] } };
  expect(body.kind).toBe('llm.publish');
  expect(body.params.platforms).toEqual(['youtube', 'tiktok']);
});

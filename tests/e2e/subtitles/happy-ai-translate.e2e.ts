import { expect, test } from '@playwright/test';
import { apiFixture, openApp } from '../support/app';
import { combine, llmReplies } from '../support/llm';
import { pickOption } from '../support/select';
import { goToSubtitles, jobBodies, PROJECT, subtitleReplies } from '../support/subtitles';

test('Traducir al portugués con el asistente y aceptar la pista entera', async ({ page }) => {
  const translated = { ...apiFixture('subtitles/doc'), tracks: { pt: apiFixture<{ cues: unknown[] }>('llm/subtitles_translate').cues } };
  const apply = ({ method, path }: { method: string; path: string }) =>
    method === 'POST' && path === '/llm/subtitles/7/apply' ? translated : undefined;
  const { calls } = await openApp(page, { replies: combine(apply, llmReplies(), subtitleReplies({ projects: [PROJECT] })) });
  await goToSubtitles(page);
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();

  await pickOption(page, 'Traducir a', 'Português');
  await page.getByRole('button', { name: 'Traducir', exact: true }).click();
  await expect(page.getByText('olá a todos')).toBeVisible();
  await page.getByRole('button', { name: 'Aceptar la pista' }).click();

  await expect(page.getByText('Cambios aplicados.')).toBeVisible();
  expect(jobBodies(calls)).toContainEqual({ kind: 'llm.subtitles_translate', params: { project_id: 7, language: 'pt' } });
  expect(calls.find((call) => call.path === '/llm/subtitles/7/apply')?.body).toEqual({ job_id: 900, accepted: null });
});

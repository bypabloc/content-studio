import { expect, test } from '@playwright/test';
import { apiFixture, openApp } from '../support/app';
import { combine, llmReplies } from '../support/llm';
import { goToSubtitles, jobBodies, PROJECT, subtitleReplies } from '../support/subtitles';

test('Corregir con un glosario: el cue corregido se aplica y el editor lo muestra', async ({ page }) => {
  const doc = apiFixture<{ cues: { id: number; text: string }[] }>('subtitles/doc');
  const corrected = { ...doc, cues: doc.cues.map((cue) => (cue.id === 1 ? { ...cue, text: 'hola a Klinikae' } : cue)) };
  const apply = ({ method, path }: { method: string; path: string }) =>
    method === 'POST' && path === '/llm/subtitles/7/apply' ? corrected : undefined;
  const { calls } = await openApp(page, { replies: combine(apply, llmReplies(), subtitleReplies({ projects: [PROJECT] })) });
  await goToSubtitles(page);
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();

  await page.getByRole('textbox', { name: 'Glosario: un nombre por línea' }).fill('Klinikae');
  await page.getByRole('button', { name: 'Corregir transcripción' }).click();
  await page.getByRole('button', { name: 'Aplicar lo elegido' }).click();

  await expect(page.getByLabel('Texto del subtítulo', { exact: true }).first()).toHaveValue('hola a Klinikae');
  await expect.poll(() => jobBodies(calls)).toContainEqual({ kind: 'llm.subtitles_correct', params: { project_id: 7, glossary: ['Klinikae'] } });
  expect(calls.find((call) => call.path === '/llm/subtitles/7/apply')?.body).toEqual({ job_id: 900, accepted: [1] });
});

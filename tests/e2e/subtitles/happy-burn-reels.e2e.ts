import { expect, test } from '@playwright/test';
import { openApp } from '../support/app';
import { pickOption } from '../support/select';
import { goToSubtitles, jobBodies, PROJECT, subtitleReplies } from '../support/subtitles';

test('AC-6: el estilo de redes (reels) se guarda con el documento, y Quemar encola el trabajo de quemado', async ({
  page,
}) => {
  const { calls } = await openApp(page, { replies: subtitleReplies({ projects: [PROJECT] }) });
  await goToSubtitles(page);
  await page.getByRole('button', { name: 'Abrir', exact: true }).click();

  await pickOption(page, 'Estilo', 'Redes (reels)');
  await expect
    .poll(() => calls.find((call) => call.method === 'PUT' && call.path === '/subtitles/7')?.body)
    .toEqual(expect.objectContaining({ style: expect.objectContaining({ mode: 'social' }) }));

  await page.getByRole('button', { name: 'Quemar subtítulos', exact: true }).click();
  await expect.poll(() => jobBodies(calls)).toContainEqual({ kind: 'subtitles.burn', params: { project_id: 7 } });
});

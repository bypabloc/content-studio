import { expect, test } from '@playwright/test';

import { apiFixture, openApp } from '../support/app';
import { editorReplies, editorState } from '../support/editor';

test('AC-7: transcribir la mezcla con hablantes y la pista de subtítulos dibuja cada cue con el color y el nombre de su hablante', async ({
  page,
}) => {
  const state = editorState();
  const fallback = editorReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => {
      if (call.method === 'GET' && call.path === '/engines') return apiFixture('transcription/engines');
      if (call.method === 'GET' && call.path === '/subtitles/7') return apiFixture('subtitles/doc-speakers');
      if (call.method === 'POST' && call.path === '/jobs') {
        const kind = (call.body as { kind: string }).kind;
        return kind === 'transcribe' ? { id: 11, status: 'queued', progress: 0 } : { id: 10, status: 'queued', progress: 0 };
      }
      if (call.method === 'GET' && call.path === '/jobs/10') {
        return { id: 10, kind: 'editor.render', status: 'done', progress: 1, result: { output: 'C:/fake/out/mix.wav' } };
      }
      if (call.method === 'GET' && call.path === '/jobs/11') return { id: 11, kind: 'transcribe', status: 'done', progress: 1, result: null };
      if (call.method === 'POST' && call.path === '/subtitles/from-transcript') return { id: 7, name: 'mix' };
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();

  // AC-7: el trabajo transcribe lleva diarize: true cuando el interruptor está encendido
  await page.getByRole('switch', { name: 'Identificar hablantes', exact: true }).click();
  await page.getByRole('button', { name: 'Transcribir la mezcla del editor', exact: true }).click();
  await expect
    .poll(() => calls.find((call) => call.method === 'POST' && call.path === '/jobs' && (call.body as { kind: string }).kind === 'transcribe')?.body)
    .toEqual({ kind: 'transcribe', params: { input: 'C:/fake/out/mix.wav', model: 'large-v3-turbo', language: 'auto', diarize: true } });

  // AC-7: la pista dibuja un bloque por cue, con el color y el nombre de su hablante
  await expect(page.getByRole('group', { name: 'hola a todos', exact: true })).toHaveCSS('background-color', 'rgb(37, 99, 235)');
  await expect(page.getByRole('group', { name: 'buenas tardes', exact: true })).toHaveCSS('background-color', 'rgb(220, 38, 38)');
  await expect(page.getByText('Ana', { exact: true }).first()).toBeVisible();
});

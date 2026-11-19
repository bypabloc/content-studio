import { expect, test } from '@playwright/test';
import { emitEvent, hasListener, openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState } from '../support/narration';

test('AC-9: un archivo que no es .txt ni .json da el error del catálogo y no encola nada', async ({ page }) => {
  const state: NarrationState = { jobs: [] };
  const { calls } = await openApp(page, { replies: narrationReplies(state) });
  await goToNarration(page);
  await expect.poll(() => hasListener(page, 'tauri://drag-drop')).toBe(true);

  await emitEvent(page, 'tauri://drag-drop', { type: 'drop', paths: ['C:/guiones/a.mp3'], position: { x: 0, y: 0 } });

  await expect(page.getByText('Solo se importan .txt y .json. Estos no: a.mp3')).toBeVisible();
  expect(calls.some((call) => call.method === 'POST' && call.path === '/jobs')).toBe(false);
});

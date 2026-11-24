import { expect, test } from '@playwright/test';

import { openApp } from '../support/app';
import { editorReplies, editorState } from '../support/editor';
import { narrationReplies, take, type NarrationState } from '../support/narration';

test('AC-7: abre una toma de Narración en un proyecto nuevo del Editor', async ({ page }) => {
  const narration: NarrationState = { jobs: [take(7, 'voxcpm2')] };
  const project = editorState();
  project.project.doc = {
    version: 3,
    name: 'Proyecto nuevo',
    sample_rate: 48000,
    canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' },
    tracks: [],
    clips: [],
    markers: [],
    transitions: [],
  };
  const narrationResponse = narrationReplies(narration);
  const editorResponse = editorReplies(project);
  const wav = 'D:/out/narration/2026-11-19-7-hola/voxcpm2-expert.wav';
  const { calls } = await openApp(page, {
    replies: (call) => {
      const narrationReply = narrationResponse(call);
      if (narrationReply !== undefined) return narrationReply;
      if (call.method === 'POST' && call.path === '/editor/projects') return project.project;
      if (call.method === 'GET' && call.path === '/fs/info') return { duration: 3, kind: 'audio', has_audio: true };
      return editorResponse(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Narración' }).click();
  const result = page.getByRole('region', { name: 'Resultado' });
  await expect(result.getByRole('button', { name: 'Abrir en Editor' })).toBeVisible();
  await result.getByRole('button', { name: 'Abrir en Editor' }).click();

  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/editor/projects')).toBe(true);
  await expect.poll(() => calls.some((call) => call.method === 'GET' && call.path === '/fs/info')).toBe(true);
  const importedPath = new URLSearchParams(calls.find((call) => call.method === 'GET' && call.path === '/fs/info')?.search).get('path');
  expect(importedPath).toBe(wav);
  await expect(page.getByRole('button', { name: /voxcpm2-expert\.wav:/ })).toBeVisible();
  await expect(page.getByRole('main').getByRole('heading', { level: 3 }).first()).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.location.hash)).toBe('#/editor');
});

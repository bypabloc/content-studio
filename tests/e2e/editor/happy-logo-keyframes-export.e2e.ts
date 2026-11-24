import { readFileSync } from 'node:fs';

import { expect, test } from '@playwright/test';

import type { Binary } from '../support/app';
import { apiFixture, openApp } from '../support/app';
import { editorReplies, editorState, requestBodies } from '../support/editor';

function image(path: string): Binary {
  return { contentType: 'image/png', body: readFileSync(new URL(path, import.meta.url)) };
}

test('AC-7: edita un keyframe del logo y exporta el proyecto como video', async ({ page }) => {
  const state = editorState();
  state.project = apiFixture<typeof state.project>('editor/project-logo-keyframes');
  const fallback = editorReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => {
      const source = new URL(call.search, 'http://127.0.0.1').searchParams.get('source');
      if (call.method === 'GET' && call.path === '/editor/projects/media' && source === 'D:/media/logo.png') {
        return image('../../../server/tests/fixtures/editor/parity-red-alpha.png');
      }
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  const workspace = page.getByRole('region', { name: 'Proyecto demo' });
  await expect(workspace).toBeVisible();
  await page.getByRole('button', { name: 'logo.png: 0.0–5.0' }).click();
  await page.getByRole('button', { name: 'Ir al siguiente keyframe' }).click();
  await page.getByRole('spinbutton', { name: 'Posición X' }).fill('220');
  await expect.poll(() => {
    const doc = state.project.doc;
    const clip = doc.clips[0] as { keyframes: { x: Array<{ t: number; value: number }> } };
    return clip.keyframes.x.find((frame) => frame.t === 2)?.value;
  }).toBe(220);

  await page.getByRole('button', { name: 'Exportar…' }).click();
  await page.getByRole('dialog', { name: 'Exportar proyecto' }).getByRole('button', { name: 'Iniciar exportación' }).click();
  await expect.poll(() => requestBodies(calls, '/jobs', 'POST')).toContainEqual(
    expect.objectContaining({ kind: 'editor.render', params: expect.objectContaining({ format: 'mp4-h264' }) }),
  );
});

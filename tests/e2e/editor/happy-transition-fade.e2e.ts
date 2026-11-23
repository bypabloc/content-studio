import { readFileSync } from 'node:fs';

import { expect, test } from '@playwright/test';

import type { Binary } from '../support/app';
import { apiFixture, openApp } from '../support/app';
import { editorReplies, editorState, requestBodies } from '../support/editor';

function image(path: string): Binary {
  return { contentType: 'image/png', body: readFileSync(new URL(path, import.meta.url)) };
}

test('AC-3: aplica un fundido en el corte visual y lo incluye en la exportación', async ({ page }) => {
  const state = editorState();
  state.project = apiFixture<typeof state.project>('editor/project-transition');
  const fallback = editorReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => {
      const source = new URL(call.search, 'http://127.0.0.1').searchParams.get('source');
      if (call.method === 'GET' && call.path === '/editor/projects/media' && source?.endsWith('.png')) {
        return image('../../../server/tests/fixtures/editor/parity-red-alpha.png');
      }
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  const workspace = page.getByRole('region', { name: 'Proyecto demo' });
  await expect(workspace).toBeVisible();
  const lane = page.getByRole('group', { name: 'Pista Video', exact: true });
  const fade = page.getByRole('group', { name: 'Transiciones', exact: true }).getByRole('button', { name: 'Fundido', exact: true });
  await lane.scrollIntoViewIfNeeded();
  await fade.dragTo(lane, { targetPosition: { x: 240, y: 45 } });
  await expect.poll(() => state.project.doc.transitions).toEqual([
    expect.objectContaining({ type: 'fade', a: 'first', b: 'second', track: 'video', duration: 0.5 }),
  ]);
  await expect(page.getByRole('group', { name: 'Transición Fundido' })).toBeVisible();

  await page.getByRole('button', { name: 'Exportar…' }).click();
  await page.getByRole('dialog', { name: 'Exportar proyecto' }).getByRole('button', { name: 'Iniciar exportación' }).click();
  await expect.poll(() => requestBodies(calls, '/jobs', 'POST')).toContainEqual(
    expect.objectContaining({ kind: 'editor.render', params: expect.objectContaining({ format: 'mp4-h264' }) }),
  );
});

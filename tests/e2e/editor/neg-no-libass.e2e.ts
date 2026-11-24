import { readFileSync } from 'node:fs';

import { expect, test } from '@playwright/test';

import type { Binary } from '../support/app';
import { apiFixture, openApp } from '../support/app';
import { editorReplies, editorState } from '../support/editor';

function image(path: string): Binary {
  return { contentType: 'image/png', body: readFileSync(new URL(path, import.meta.url)) };
}

test('AC-6: deshabilita quemar subtítulos cuando falta libass', async ({ page }) => {
  const state = editorState();
  state.project = apiFixture<typeof state.project>('editor/project-logo-keyframes');
  state.project.doc.version = 3;
  for (const clip of state.project.doc.clips) clip.speed = 1;
  state.project.doc.tracks.push({
    id: 'subtitles',
    kind: 'subtitles',
    name: 'Subtítulos',
    subtitles_project: '7',
    locked: false,
  });
  const fallback = editorReplies(state);
  await openApp(page, {
    replies: (call) => {
      if (call.method === 'GET' && call.path === '/subtitles') return [{ id: 7, name: 'demo' }];
      if (call.method === 'GET' && call.path === '/system') return { subtitles_filter: false };
      if (call.method === 'GET' && call.path === '/subtitles/7') return apiFixture('subtitles/doc');
      if (call.method === 'GET' && call.path === '/subtitles/fonts') return [];
      if (call.method === 'GET' && call.path === '/editor/projects/media') {
        return image('../../../server/tests/fixtures/editor/parity-red-alpha.png');
      }
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  await page.getByRole('button', { name: 'Exportar…' }).click();
  const dialog = page.getByRole('dialog', { name: 'Exportar proyecto' });
  const subtitles = dialog.getByRole('combobox', { name: 'Subtítulos de la exportación' });
  await subtitles.click();
  const burn = page.getByRole('option', { name: 'Quemar en el video' });

  await expect.poll(async () => (await burn.getAttribute('aria-disabled')) === 'true' || burn.isDisabled()).toBe(true);
  await expect(dialog.getByText(/Este ffmpeg no trae libass/)).toBeVisible();
});

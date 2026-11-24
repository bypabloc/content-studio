import { readFileSync } from 'node:fs';

import { expect, test } from '@playwright/test';

import type { Binary } from '../support/app';
import { apiFixture, openApp } from '../support/app';
import { editorReplies, editorState } from '../support/editor';

function image(path: string): Binary {
  return { contentType: 'image/png', body: readFileSync(new URL(path, import.meta.url)) };
}

test('AC-2: crea un lower-third rasterizado y conserva el texto en el proyecto', async ({ page }) => {
  const state = editorState();
  state.project = apiFixture<typeof state.project>('editor/project-logo-keyframes');
  state.project.doc.version = 3;
  for (const clip of state.project.doc.clips) clip.speed = 1;
  const fallback = editorReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => {
      if (call.method === 'GET' && call.path === '/subtitles/fonts') return [];
      if (call.method === 'POST' && call.path === '/editor/projects/media') return { src: 'media/title.png' };
      if (call.method === 'GET' && call.path === '/editor/projects/media') {
        return image('../../../server/tests/fixtures/editor/parity-red-alpha.png');
      }
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  await expect(page.getByRole('region', { name: 'Proyecto demo' })).toBeVisible();
  await page.getByRole('button', { name: 'Agregar texto' }).click();
  await page.getByRole('region', { name: 'Texto y títulos' })
    .getByRole('textbox', { name: 'Texto', exact: true })
    .fill('María · Directora');

  await expect.poll(() => {
    const clip = state.project.doc.clips.find((item) => item.media === 'text');
    return (clip?.text as { content?: string } | undefined)?.content;
  }).toBe('María · Directora');
  await expect.poll(() => calls.some((call) => call.method === 'POST' && call.path === '/editor/projects/media')).toBe(true);
  await expect.poll(() => state.project.doc.clips.find((item) => item.media === 'text')?.src).toBe('media/title.png');
});

import { expect, test } from '@playwright/test';

import { apiFixture, openApp, setDialogPick } from '../support/app';
import { editorReplies, editorState } from '../support/editor';

test('AC-4: detecta la fuente ausente del proxy y permite reasignar el video', async ({ page }) => {
  const state = editorState();
  state.project = apiFixture<typeof state.project>('editor/project-proxy-missing');
  const fallback = editorReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => {
      const source = new URL(call.search, 'http://127.0.0.1').searchParams.get('source');
      if (call.method === 'GET' && call.path === '/editor/projects/media' && source === 'D:/missing/logo.mp4') {
        return { failed: { status: 404, body: { error: { code: 'fs_media_not_found' } } } };
      }
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  const alert = page.getByRole('alert');
  await expect(alert.getByText('Fuente no encontrada: D:/missing/logo.mp4')).toBeVisible();
  await expect.poll(() => calls.some((call) => {
    const query = new URL(call.search, 'http://127.0.0.1').searchParams;
    return call.method === 'GET' && call.path === '/editor/projects/media' && query.get('source') === 'D:/missing/logo.mp4';
  })).toBe(true);

  await setDialogPick(page, ['D:/media/logo-restaurado.mp4']);
  await alert.getByRole('button', { name: 'Buscar…' }).click();
  await expect(alert).toHaveCount(0);
  await expect.poll(() => (state.project.doc.clips[0] as { src: string }).src).toBe('D:/media/logo-restaurado.mp4');
});

import { expect, test } from '@playwright/test';
import { emitEvent, hasListener, openApp } from '../support/app';
import { goToNarration, narrationReplies, type NarrationState } from '../support/narration';

test('AC-9: soltar dos guiones .json encola dos trabajos, uno por archivo', async ({ page }) => {
  const state: NarrationState = { jobs: [] };
  const { calls } = await openApp(page, { replies: narrationReplies(state) });
  await goToNarration(page);
  // Soltar antes de que llegue el catálogo no encola nada (ready = motor y estilo): esperar el motor primero.
  await expect(page.getByRole('combobox', { name: 'Motor' })).toHaveValue('voxcpm2');
  await expect.poll(() => hasListener(page, 'tauri://drag-drop')).toBe(true);

  await emitEvent(page, 'tauri://drag-drop', {
    type: 'drop',
    paths: ['C:/guiones/a.json', 'C:/guiones/b.json'],
    position: { x: 0, y: 0 },
  });

  await expect
    .poll(() => calls.filter((call) => call.method === 'POST' && call.path === '/jobs').map((call) => call.body))
    .toEqual([
      { kind: 'narration', params: expect.objectContaining({ file: ['C:/guiones/a.json'] }) },
      { kind: 'narration', params: expect.objectContaining({ file: ['C:/guiones/b.json'] }) },
    ]);
});

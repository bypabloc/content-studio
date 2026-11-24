import { readFileSync } from 'node:fs';

import { expect, test } from '@playwright/test';

import type { Binary } from '../support/app';
import { openApp } from '../support/app';
import { editorReplies, editorState, requestBodies } from '../support/editor';
import { pickOption } from '../support/select';

function image(path: string): Binary {
  return { contentType: 'image/png', body: readFileSync(new URL(path, import.meta.url)) };
}

function visualClip(id: string, track: string, source: string): Record<string, unknown> {
  return {
    id,
    track,
    src: source,
    src_in: 0,
    src_out: 5,
    start: 0,
    fade_in: 0,
    fade_out: 0,
    speed: 1,
    media: 'image',
    transform: {
      x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
      crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
    },
    keyframes: {},
  };
}

test('AC-3 y AC-5: activa chroma, mezcla capas y exporta el proyecto', async ({ page }) => {
  const state = editorState();
  state.project.doc = {
    version: 3,
    name: 'demo',
    sample_rate: 48000,
    canvas: { width: 800, height: 450, fps: 24, background: '#101820' },
    tracks: [
      { id: 'base', kind: 'video', name: 'Base', opacity: 1, hidden: false, locked: false },
      { id: 'key', kind: 'video', name: 'Chroma', opacity: 1, hidden: false, locked: false },
    ],
    clips: [
      visualClip('base', 'base', 'parity-effects-base.png'),
      visualClip('key', 'key', 'parity-effects-chroma.png'),
    ],
    markers: [],
    transitions: [],
  };
  const fallback = editorReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => {
      const source = new URL(call.search, 'http://127.0.0.1').searchParams.get('source');
      if (call.method === 'GET' && call.path === '/editor/projects/media') {
        if (source?.endsWith('parity-effects-base.png')) return image('../../../server/tests/fixtures/editor/parity-effects-base.png');
        if (source?.endsWith('parity-effects-chroma.png')) return image('../../../server/tests/fixtures/editor/parity-effects-chroma.png');
      }
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  await expect(page.getByRole('region', { name: 'demo' })).toBeVisible();
  await page.getByRole('button', { name: /parity-effects-chroma\.png/ }).click();
  await page.getByRole('button', { name: 'Activar chroma key' }).click();
  await page.getByRole('textbox', { name: 'Color de clave' }).fill('#008000');
  await pickOption(page, 'Modo de fusión', 'Multiplicar');

  await expect.poll(() => {
    const clip = state.project.doc.clips.find((item) => item.id === 'key');
    const chroma = clip?.chroma as { color?: string } | undefined;
    return [clip?.blend_mode, chroma?.color];
  }).toEqual(['multiply', '#008000']);

  await page.getByRole('button', { name: 'Exportar…' }).click();
  await page.getByRole('dialog', { name: 'Exportar proyecto' }).getByRole('button', { name: 'Iniciar exportación' }).click();
  await expect.poll(() => requestBodies(calls, '/jobs', 'POST')).toContainEqual(
    expect.objectContaining({ kind: 'editor.render', params: expect.objectContaining({ format: 'mp4-h264' }) }),
  );
});

import { readFileSync } from 'node:fs';

import { expect, test } from '@playwright/test';

import type { Binary } from '../support/app';
import { editorReplies, editorState } from '../support/editor';
import { openApp } from '../support/app';
import { pickOption } from '../support/select';

// cspell:ignore Ssim SSIM: métrica estructural de similitud entre imágenes.
type Fixture = {
  sample_times: number[];
  blend_modes: Array<[string, string]>;
  doc: Record<string, unknown>;
};
const fixture = JSON.parse(
  readFileSync(new URL('../../../server/tests/fixtures/editor/parity-effects.json', import.meta.url), 'utf8'),
) as Fixture;
const fixtureRoot = '../../../server/tests/fixtures/editor/';

function binary(path: string, contentType = 'image/png'): Binary {
  return { contentType, body: readFileSync(new URL(fixtureRoot + path, import.meta.url)) };
}

function frameName(mode: string): string {
  return `parity-effects-${mode}.png`;
}

async function previewSsim(page: import('@playwright/test').Page, label: string, preview: Buffer): Promise<number> {
  return page.evaluate(async ({ alt, previewData }) => {
    const decode = (src: string) => new Promise<HTMLImageElement>((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = reject;
      image.src = src;
    });
    const [rendered, reference] = await Promise.all([
      decode(`data:image/png;base64,${previewData}`),
      Promise.resolve(document.querySelector<HTMLImageElement>(`img[alt="${alt}"]`)),
    ]);
    if (!reference?.complete || !reference.naturalWidth) throw new Error('La referencia exacta no cargó.');
    const { naturalWidth: width, naturalHeight: height } = rendered;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('No se pudo leer la comparación de imagen.');
    context.drawImage(rendered, 0, 0, width, height);
    const actual = context.getImageData(0, 0, width, height).data;
    context.clearRect(0, 0, width, height);
    context.drawImage(reference, 0, 0, width, height);
    const expected = context.getImageData(0, 0, width, height).data;
    const c1 = 6.5025;
    const c2 = 58.5225;
    let total = 0;
    let windows = 0;
    for (let top = 0; top < height; top += 8) {
      for (let left = 0; left < width; left += 8) {
        const pixels: Array<[number, number]> = [];
        let meanA = 0;
        let meanB = 0;
        for (let y = top; y < Math.min(top + 8, height); y += 1) {
          for (let x = left; x < Math.min(left + 8, width); x += 1) {
            const offset = (y * width + x) * 4;
            const a = 0.2126 * actual[offset] + 0.7152 * actual[offset + 1] + 0.0722 * actual[offset + 2];
            const b = 0.2126 * expected[offset] + 0.7152 * expected[offset + 1] + 0.0722 * expected[offset + 2];
            pixels.push([a, b]);
            meanA += a;
            meanB += b;
          }
        }
        meanA /= pixels.length;
        meanB /= pixels.length;
        let varianceA = 0;
        let varianceB = 0;
        let covariance = 0;
        for (const [a, b] of pixels) {
          varianceA += (a - meanA) ** 2;
          varianceB += (b - meanB) ** 2;
          covariance += (a - meanA) * (b - meanB);
        }
        varianceA /= pixels.length;
        varianceB /= pixels.length;
        covariance /= pixels.length;
        total += ((2 * meanA * meanB + c1) * (2 * covariance + c2)) /
          ((meanA ** 2 + meanB ** 2 + c1) * (varianceA + varianceB + c2));
        windows += 1;
      }
    }
    return total / windows;
  }, { alt: label, previewData: preview.toString('base64') });
}

test('AC-3 y AC-5: el visor conserva color, LUT, chroma y fusión en tres tiempos', async ({ page }) => {
  // Calcula el SSIM de tres cuadros por cada efecto: solo ya tarda unos 29 s y con 12 workers pasaba los 30 s (spec 023).
  test.setTimeout(90_000);
  const state = editorState();
  state.project.doc = fixture.doc;
  const fallback = editorReplies(state);
  const { calls } = await openApp(page, {
    replies: (call) => {
      const query = new URL(call.search, 'http://127.0.0.1').searchParams;
      if (call.method === 'GET' && call.path === '/editor/projects/media') {
        const source = query.get('source');
        if (source?.endsWith('.png')) return binary(source);
      }
      if (call.method === 'GET' && call.path === '/editor/projects/luts') {
        const source = query.get('source');
        if (source) return binary(source, 'text/plain; charset=utf-8');
      }
      if (call.method === 'GET' && call.path === '/editor/projects/frame') {
        const blend = (state.project.doc.clips as Array<{ id: string; blend_mode?: string }>).find(
          (clip) => clip.id === 'blend',
        );
        return binary(frameName(blend?.blend_mode ?? 'normal'));
      }
      return fallback(call);
    },
  });

  await page.getByRole('navigation').getByRole('link', { name: 'Editor' }).click();
  await page.getByRole('button', { name: 'Abrir demo' }).click();
  const workspace = page.getByRole('region', { name: 'Paridad de efectos' });
  await expect(workspace).toBeVisible();
  await page.getByRole('button', { name: /parity-red-alpha\.png: 0\.0–24\.0/ }).last().click();
  const stage = page.getByRole('group', { name: 'Lienzo del proyecto' });
  await stage.getByRole('img').evaluate((element) => ((element as HTMLElement).style.display = 'none'));
  await stage.getByRole('button').evaluateAll((elements) => {
    elements.forEach((element) => ((element as HTMLElement).style.display = 'none'));
  });

  const playhead = page.getByRole('img', { name: 'Cabezal de reproducción' });
  const nextKeyframe = page.getByRole('button', { name: 'Ir al siguiente keyframe' });
  const exactFrame = page.getByRole('button', { name: 'Ver fotograma exacto' });
  for (const [modeIndex, [mode, label]] of fixture.blend_modes.entries()) {
    if (mode !== 'normal') await pickOption(page, 'Modo de fusión', label);
    await expect.poll(() => {
      const blend = (state.project.doc.clips as Array<{ id: string; blend_mode?: string }>).find(
        (clip) => clip.id === 'blend',
      );
      return blend?.blend_mode ?? 'normal';
    }).toBe(mode);
    for (const [sampleIndex, sample] of fixture.sample_times.entries()) {
      const time = modeIndex * fixture.sample_times.length + sample;
      await nextKeyframe.click();
      await expect.poll(async () => {
        const style = await playhead.getAttribute('style') ?? '';
        return Number.parseFloat(style.match(/left:\s*([\d.]+)px/)?.[1] ?? '0');
      }).toBe(time * 80);
      if (modeIndex === 0 && sampleIndex === 0) await exactFrame.click();
      const alt = `Fotograma exacto en ${time.toFixed(2)} s`;
      const reference = page.getByRole('img', { name: alt });
      await expect(reference).toBeVisible();
      await expect.poll(() => reference.evaluate((element) => (element as HTMLImageElement).naturalWidth)).toBe(800);
      const canvas = page.locator('canvas[aria-label="Vista previa del proyecto"]');
      await expect.poll(async () => previewSsim(page, alt, await canvas.screenshot()), {
        message: `SSIM de ${mode} en ${time} s`,
      }).toBeGreaterThanOrEqual(0.95);
    }
  }

  const frames = calls.filter((call) => call.method === 'GET' && call.path === '/editor/projects/frame');
  expect(frames.map((call) => new URL(call.search, 'http://127.0.0.1').searchParams.get('t'))).toEqual(
    Array.from({ length: fixture.blend_modes.length * fixture.sample_times.length }, (_, index) =>
      String(index + 0.5),
    ),
  );
});

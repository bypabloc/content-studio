import { webcrypto } from 'node:crypto';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { TextStyle } from '@/features/editor/model/types';
import { rasterizeText } from '@/features/editor/text/rasterize';

type DrawContext = {
  font: string;
  textAlign: CanvasTextAlign;
  textBaseline: CanvasTextBaseline;
  fillStyle: string | CanvasGradient | CanvasPattern;
  strokeStyle: string | CanvasGradient | CanvasPattern;
  lineWidth: number;
  shadowColor: string;
  shadowBlur: number;
  shadowOffsetX: number;
  shadowOffsetY: number;
  commands: unknown[];
  measureText: (text: string) => TextMetrics;
  clearRect: (...args: number[]) => void;
  fillText: (...args: [string, number, number]) => void;
  strokeText: (...args: [string, number, number]) => void;
  beginPath: () => void;
  roundRect: (...args: number[]) => void;
  fill: () => void;
  save: () => void;
  restore: () => void;
};

class CanvasStub {
  static latest: CanvasStub;
  static noContext = false;
  readonly context: DrawContext;
  contextOptions: CanvasRenderingContext2DSettings | undefined;

  constructor(readonly width: number, readonly height: number) {
    CanvasStub.latest = this;
    const commands: unknown[] = [];
    this.context = {
      font: '',
      textAlign: 'left',
      textBaseline: 'alphabetic',
      fillStyle: '#000000',
      strokeStyle: '#000000',
      lineWidth: 0,
      shadowColor: 'transparent',
      shadowBlur: 0,
      shadowOffsetX: 0,
      shadowOffsetY: 0,
      commands,
      measureText: (text) => ({
        width: text.length * 10,
        actualBoundingBoxAscent: 18,
        actualBoundingBoxDescent: 5,
      }) as TextMetrics,
      clearRect: (...args) => commands.push(['clearRect', ...args]),
      fillText: (...args) => commands.push(['fillText', ...args]),
      strokeText: (...args) => commands.push(['strokeText', ...args]),
      beginPath: () => commands.push(['beginPath']),
      roundRect: (...args) => commands.push(['roundRect', ...args]),
      fill: () => commands.push(['fill']),
      save: () => commands.push(['save']),
      restore: () => commands.push(['restore']),
    };
  }

  getContext(_kind: '2d', options?: CanvasRenderingContext2DSettings): DrawContext | null {
    this.contextOptions = options;
    return CanvasStub.noContext ? null : this.context;
  }

  convertToBlob(options?: ImageEncodeOptions): Promise<Blob> {
    return Promise.resolve(new Blob([JSON.stringify(this.context.commands)], { type: options?.type }));
  }
}

const STYLE: TextStyle = {
  content: 'Hola mundo',
  font: 'Inter',
  weight: 700,
  size: 48,
  color: '#ffffff',
  stroke: { width: 2, color: '#000000' },
  shadow: { x: 1, y: 2, blur: 3, color: '#00000080' },
  align: 'center',
  line_height: 1.2,
  max_width: 80,
};

beforeEach(() => {
  CanvasStub.noContext = false;
  vi.stubGlobal('crypto', webcrypto);
  vi.stubGlobal('OffscreenCanvas', CanvasStub as unknown as typeof OffscreenCanvas);
});

afterEach(() => vi.unstubAllGlobals());

describe('rasterizeText', () => {
  it('AC-2: rasteriza texto en PNG transparente ajustado al contenido', async () => {
    const raster = await rasterizeText(STYLE);

    expect(raster.blob.type).toBe('image/png');
    expect(raster.width).toBeGreaterThan(0);
    expect(raster.height).toBeGreaterThan(0);
    expect(CanvasStub.latest.contextOptions).toEqual({ alpha: true });
    expect(CanvasStub.latest.context.commands).toContainEqual(['fillText', 'Hola', expect.any(Number), expect.any(Number)]);
    expect(CanvasStub.latest.context.commands).toContainEqual(['strokeText', 'Hola', expect.any(Number), expect.any(Number)]);
  });

  it('AC-2: conserva el hash al mover el clip y lo cambia cuando cambia el texto', async () => {
    const first = await rasterizeText(STYLE);
    const same = await rasterizeText({ ...STYLE });
    const changed = await rasterizeText({ ...STYLE, content: 'Hola mundo nuevo' });

    expect(first.hash).toBe(same.hash);
    expect(first.hash).not.toBe(changed.hash);
    expect(first.hash).toMatch(/^[a-f0-9]{64}$/);
  });

  it('admite líneas vacías, contorno de caja y familias con comillas escapadas', async () => {
    await rasterizeText({
      ...STYLE,
      content: '  ',
      font: 'A"B',
      box: { color: '#00000080', padding: 8, radius: 10 },
    });

    expect(CanvasStub.latest.context.commands).toContainEqual(['roundRect', 0, 0, expect.any(Number), expect.any(Number), 10]);
    expect(CanvasStub.latest.context.font).toContain('A\\"B');
  });

  it('informa cuando el navegador no entrega un contexto 2D', async () => {
    CanvasStub.noContext = true;

    await expect(rasterizeText(STYLE)).rejects.toThrow('No se pudo crear el contexto de texto.');

    CanvasStub.noContext = false;
  });
});

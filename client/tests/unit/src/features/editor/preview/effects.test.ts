import { describe, expect, it, vi } from 'vitest';

import { createPreviewEffects } from '@/features/editor/preview/effects';
import type { VisualClip } from '@/features/editor/model/types';
import type { Lut3D } from '@/features/editor/preview/lut';

function context(textures: Array<WebGLTexture | null> = [{} as WebGLTexture]): WebGL2RenderingContext {
  return {
    TEXTURE1: 33985,
    TEXTURE2: 33986,
    TEXTURE_2D: 3553,
    TEXTURE_3D: 32879,
    TEXTURE_MIN_FILTER: 10241,
    TEXTURE_MAG_FILTER: 10240,
    TEXTURE_WRAP_S: 10242,
    TEXTURE_WRAP_T: 10243,
    TEXTURE_WRAP_R: 32882,
    RGB8: 32849,
    RGB: 6407,
    UNSIGNED_BYTE: 5121,
    NEAREST: 9728,
    LINEAR: 9729,
    CLAMP_TO_EDGE: 33071,
    RGBA: 6408,
    BLEND: 3042,
    ONE: 1,
    ONE_MINUS_SRC_ALPHA: 771,
    drawingBufferWidth: 8,
    drawingBufferHeight: 8,
    createTexture: vi.fn(() => textures.shift() ?? null),
    activeTexture: vi.fn(),
    bindTexture: vi.fn(),
    texParameteri: vi.fn(),
    texImage3D: vi.fn(),
    uniform1i: vi.fn(),
    uniform1f: vi.fn(),
    uniform4f: vi.fn(),
    copyTexImage2D: vi.fn(),
    disable: vi.fn(),
    enable: vi.fn(),
    blendFunc: vi.fn(),
    deleteTexture: vi.fn(),
  } as unknown as WebGL2RenderingContext;
}

const uniform = Object.fromEntries([
  'u_background', 'u_lut', 'u_color', 'u_chromaColor', 'u_chromaBlend', 'u_hasChroma',
  'u_despill', 'u_lutDomainMin', 'u_lutDomainMax', 'u_lutSize', 'u_hasLut', 'u_blendMode',
].map((name) => [name, { name } as unknown as WebGLUniformLocation]));

const lut: Lut3D = { size: 2, data: new Uint8Array(24), domainMin: [0, 0, 0], domainMax: [1, 1, 1] };
const clip = (values: Partial<VisualClip> = {}) => ({ id: 'clip', media: 'video', ...values }) as VisualClip;

describe('efectos de vista previa', () => {
  it('usa valores predeterminados y libera la textura de fondo', () => {
    const gl = context();
    const effects = createPreviewEffects(gl, uniform);

    expect(effects.prepare(clip(), undefined)).toBe(0);
    effects.finish(0);
    effects.destroy();

    expect(gl.uniform1i).toHaveBeenCalledWith(uniform.u_blendMode, 0);
    expect(gl.deleteTexture).toHaveBeenCalledTimes(1);
  });

  it('carga una LUT una vez, configura chroma y restaura la fusión', () => {
    const background = {} as WebGLTexture;
    const lutTexture = {} as WebGLTexture;
    const gl = context([background, lutTexture]);
    const effects = createPreviewEffects(gl, uniform);
    const colored = clip({
      color: { brightness: 0.1, contrast: 1.2, saturation: 0.8, gamma: 1, lut: 'media/lut.cube' },
      chroma: { color: '#00ff00', similarity: 0.3, blend: 0.15, despill: true },
      blend_mode: 'multiply',
    });

    expect(effects.prepare(colored, lut)).toBe(1);
    expect(effects.prepare(colored, lut)).toBe(1);
    effects.finish(1);
    effects.destroy();

    expect(gl.uniform1i).toHaveBeenCalledWith(uniform.u_despill, 1);
    expect(gl.uniform1i).toHaveBeenCalledWith(uniform.u_blendMode, 1);
    expect(gl.texImage3D).toHaveBeenCalledTimes(1);
    expect(gl.copyTexImage2D).toHaveBeenCalledTimes(2);
    expect(gl.disable).toHaveBeenCalledWith(gl.BLEND);
    expect(gl.blendFunc).toHaveBeenCalledWith(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    expect(gl.deleteTexture).toHaveBeenCalledTimes(2);
  });

  it('selecciona despill azul, omite una LUT no disponible y permite crear un modo sin LUT', () => {
    const gl = context();
    const effects = createPreviewEffects(gl, uniform);
    const blueKey = clip({ chroma: { color: '#0000ff', similarity: 0.2, blend: 0.1, despill: true }, blend_mode: 'screen' });

    expect(effects.prepare(blueKey, undefined)).toBe(2);
    expect(gl.uniform1i).toHaveBeenCalledWith(uniform.u_despill, 2);
    expect(gl.uniform1i).toHaveBeenCalledWith(uniform.u_blendMode, 2);
    effects.finish(2);
    effects.destroy();
  });

  it('informa si WebGL no puede crear las texturas requeridas', () => {
    expect(() => createPreviewEffects(context([null]), uniform)).toThrow('blend texture allocation failed');
    const gl = context([{} as WebGLTexture, null]);
    const effects = createPreviewEffects(gl, uniform);

    expect(() => effects.prepare(clip({ color: { brightness: 0, contrast: 1, saturation: 1, gamma: 1, lut: 'media/a.cube' } }), lut))
      .toThrow('LUT texture allocation failed');
  });
});

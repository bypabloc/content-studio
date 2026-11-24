import type { BlendMode, ColorEffects, VisualClip } from '../model/types';
import type { Lut3D } from './lut';

type Uniforms = Record<string, WebGLUniformLocation | null>;

const DEFAULT_COLOR: ColorEffects = { brightness: 0, contrast: 1, saturation: 1, gamma: 1 };
const BLEND_IDS: Record<BlendMode, number> = {
  normal: 0, multiply: 1, screen: 2, overlay: 3, darken: 4, lighten: 5, add: 6, difference: 7,
};

function rgb(hex: string): [number, number, number] {
  return [1, 3, 5].map((index) => Number.parseInt(hex.slice(index, index + 2), 16) / 255) as [number, number, number];
}

/** Administra LUT 3D, controles de clip y la captura del fondo para modos de fusión. */
export function createPreviewEffects(gl: WebGL2RenderingContext, uniform: Uniforms) {
  const background = gl.createTexture();
  if (!background) throw new Error('WebGL2 blend texture allocation failed');
  const luts = new Map<string, WebGLTexture>();
  gl.activeTexture(gl.TEXTURE2);
  gl.bindTexture(gl.TEXTURE_2D, background);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.uniform1i(uniform.u_background, 2);
  gl.uniform1i(uniform.u_lut, 1);

  function texture(path: string, lut: Lut3D): WebGLTexture {
    let result = luts.get(path);
    if (!result) {
      result = gl.createTexture() ?? undefined;
      if (!result) throw new Error('WebGL2 LUT texture allocation failed');
      luts.set(path, result);
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_3D, result);
      gl.texParameteri(gl.TEXTURE_3D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_3D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_3D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_3D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_3D, gl.TEXTURE_WRAP_R, gl.CLAMP_TO_EDGE);
      gl.texImage3D(gl.TEXTURE_3D, 0, gl.RGB8, lut.size, lut.size, lut.size, 0, gl.RGB, gl.UNSIGNED_BYTE, lut.data);
    }
    return result;
  }

  function prepare(clip: VisualClip, lut: Lut3D | undefined): number {
    const color = clip.color ?? DEFAULT_COLOR;
    gl.uniform4f(uniform.u_color, color.brightness, color.contrast, color.saturation, color.gamma);
    const chroma = clip.chroma;
    const key = rgb(chroma?.color ?? '#00ff00');
    gl.uniform4f(uniform.u_chromaColor, ...key, chroma?.similarity ?? 0.2);
    gl.uniform1f(uniform.u_chromaBlend, chroma?.blend ?? 0.1);
    gl.uniform1i(uniform.u_hasChroma, chroma ? 1 : 0);
    const [red, green, blue] = key;
    const despill = chroma?.despill ? (green > red && green >= blue ? 1 : blue > red ? 2 : 0) : 0;
    gl.uniform1i(uniform.u_despill, despill);
    if (lut && color.lut) {
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_3D, texture(color.lut, lut));
      gl.uniform4f(uniform.u_lutDomainMin, ...lut.domainMin, 0);
      gl.uniform4f(uniform.u_lutDomainMax, ...lut.domainMax, 1);
      gl.uniform1f(uniform.u_lutSize, lut.size);
      gl.uniform1i(uniform.u_hasLut, 1);
    } else {
      gl.uniform1i(uniform.u_hasLut, 0);
    }
    const mode = BLEND_IDS[clip.blend_mode ?? 'normal'];
    gl.uniform1i(uniform.u_blendMode, mode);
    if (mode) {
      gl.activeTexture(gl.TEXTURE2);
      gl.bindTexture(gl.TEXTURE_2D, background);
      gl.copyTexImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, 0);
      gl.disable(gl.BLEND);
    }
    return mode;
  }

  function finish(mode: number): void {
    gl.uniform1i(uniform.u_blendMode, 0);
    if (mode) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    }
  }

  return {
    prepare,
    finish,
    destroy() {
      gl.deleteTexture(background);
      for (const lut of luts.values()) gl.deleteTexture(lut);
      luts.clear();
    },
  };
}

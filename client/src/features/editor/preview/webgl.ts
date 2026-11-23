import { clipLength } from '../model/validate';
import type { Canvas, Doc, TransitionType, VideoTrack, VisualClip } from '../model/types';
import { buildLayerMatrix, clipCrop, clipProperty, hasAnimatedCrop, orderedLayers } from './compositor';
import { FRAGMENT_SHADER, VERTEX_SHADER } from './shaders';
import { transitionMode } from './transitions';
import type { Compositor, TransitionLayer } from './compositor';
import type { LayerSource, LayerSourceLookup } from './useLayerSources';

// cspell:ignore fadeblack fadewhite slideleft slideright: FFmpeg transition names.

type Uniforms = Record<string, WebGLUniformLocation | null>;
type TextureEntry = { texture: WebGLTexture; source: LayerSource; uploaded: boolean };

const IDENTITY = new Float32Array([1, 0, 0, 0, 1, 0, 0, 0, 1]);

function compile(gl: WebGL2RenderingContext, type: number, source: string): WebGLShader {
  const shader = gl.createShader(type);
  if (!shader) throw new Error('WebGL2 shader allocation failed');
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) || 'WebGL2 shader compilation failed'); // i18n-ignore: mensaje interno de WebGL sin salida directa en la interfaz
  return shader;
}

function createProgram(gl: WebGL2RenderingContext): WebGLProgram {
  const program = gl.createProgram();
  if (!program) throw new Error('WebGL2 program allocation failed');
  gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERTEX_SHADER));
  gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER));
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program) || 'WebGL2 program link failed'); // i18n-ignore: mensaje interno de WebGL sin salida directa en la interfaz
  return program;
}

function getUniforms(gl: WebGL2RenderingContext, program: WebGLProgram): Uniforms {
  const names = [
    'u_matrix', 'u_shift', 'u_texture', 'u_crop', 'u_opacity', 'u_progress', 'u_transition',
    'u_role', 'u_cropMask', 'u_solid', 'u_solidColor', 'u_premultiplied',
  ];
  return Object.fromEntries(names.map((name) => [name, gl.getUniformLocation(program, name)]));
}

function rgba(hex: string): [number, number, number, number] {
  const raw = hex.replace('#', '');
  const expanded = raw.length === 3 ? raw.split('').map((part) => part + part).join('') : raw;
  const normalized = expanded.length === 8 ? expanded : expanded + 'ff';
  return [0, 2, 4, 6].map((index) => Number.parseInt(normalized.slice(index, index + 2), 16) / 255) as [number, number, number, number];
}

function dimensions(source: LayerSource): { width: number; height: number } {
  if (source instanceof HTMLVideoElement) return { width: source.videoWidth, height: source.videoHeight };
  return { width: source.naturalWidth || source.width, height: source.naturalHeight || source.height };
}

function previewSize(canvas: HTMLCanvasElement, project: Canvas): [number, number] {
  const cssWidth = canvas.clientWidth || project.width;
  const cssHeight = canvas.clientHeight || project.height;
  const scale = Math.min(1, cssWidth / project.width, cssHeight / project.height);
  const width = Math.max(1, Math.round(project.width * scale));
  const height = Math.max(1, Math.round(project.height * scale));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  return [width, height];
}

function quad(clip: VisualClip, width: number, height: number, time: number): Float32Array {
  const crop = clipCrop(clip, time);
  const animated = hasAnimatedCrop(clip);
  const x0 = animated ? 0 : crop.l * width;
  const y0 = animated ? 0 : crop.t * height;
  const x1 = animated ? width : (1 - crop.r) * width;
  const y1 = animated ? height : (1 - crop.b) * height;
  const u0 = x0 / width;
  const v0 = y0 / height;
  const u1 = x1 / width;
  const v1 = y1 / height;
  return new Float32Array([
    x0, y0, u0, v0, x1, y0, u1, v0, x1, y1, u1, v1,
    x0, y0, u0, v0, x1, y1, u1, v1, x0, y1, u0, v1,
  ]);
}

function fullQuad(): Float32Array {
  return new Float32Array([
    -1, 1, 0, 0, 1, 1, 1, 0, 1, -1, 1, 1,
    -1, 1, 0, 0, 1, -1, 1, 1, -1, -1, 0, 1,
  ]);
}

/** Crea un compositor WebGL2 y conserva texturas de video entre cuadros. */
export function createCompositor(canvas: HTMLCanvasElement): Compositor {
  const context = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true, antialias: false });
  if (!context) throw new Error('WebGL2 unavailable');
  const gl: WebGL2RenderingContext = context;
  const program = createProgram(gl);
  const uniform = getUniforms(gl, program);
  const buffer = gl.createBuffer();
  if (!buffer) throw new Error('WebGL2 buffer allocation failed');
  const position = gl.getAttribLocation(program, 'a_position');
  const texCoord = gl.getAttribLocation(program, 'a_texCoord');
  const textures = new Map<string, TextureEntry>();
  let targetTexture: WebGLTexture | null = null;
  let targetFramebuffer: WebGLFramebuffer | null = null;
  let targetSize = '';
  let destroyed = false;

  gl.useProgram(program);
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.enableVertexAttribArray(position);
  gl.enableVertexAttribArray(texCoord);
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 16, 0);
  gl.vertexAttribPointer(texCoord, 2, gl.FLOAT, false, 16, 8);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  gl.uniform1i(uniform.u_texture, 0);

  function geometry(data: Float32Array, matrix: Float32Array, shift: [number, number] = [0, 0]): void {
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.DYNAMIC_DRAW);
    gl.uniformMatrix3fv(uniform.u_matrix, false, matrix);
    gl.uniform2f(uniform.u_shift, shift[0], shift[1]);
    gl.drawArrays(gl.TRIANGLES, 0, data.length / 4);
  }

  function transition(type: TransitionType | null, progress: number, role: number): void {
    gl.uniform1i(uniform.u_transition, type ? transitionMode(type) : 0);
    gl.uniform1f(uniform.u_progress, progress);
    gl.uniform1i(uniform.u_role, role);
  }

  function upload(id: string, source: LayerSource, isVideo: boolean): WebGLTexture {
    let entry = textures.get(id);
    if (!entry) {
      const texture = gl.createTexture();
      if (!texture) throw new Error('WebGL2 texture allocation failed');
      entry = { texture, source, uploaded: false };
      textures.set(id, entry);
    }
    if (!entry.uploaded || entry.source !== source || isVideo) {
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, entry.texture);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
      entry.source = source;
      entry.uploaded = true;
    } else {
      gl.bindTexture(gl.TEXTURE_2D, entry.texture);
    }
    return entry.texture;
  }

  function drawClip(
    clip: VisualClip,
    track: VideoTrack,
    time: number,
    canvasSize: Canvas,
    source: LayerSource | undefined,
    type: TransitionType | null = null,
    progress = 0,
    role = 0,
    shift: [number, number] = [0, 0],
  ): void {
    if (!source) return;
    const isVideo = source instanceof HTMLVideoElement;
    const size = dimensions(source);
    if (isVideo) {
      const video = source as HTMLVideoElement;
      const sourceTime = clip.src_in + Math.max(0, time - clip.start);
      if (Number.isFinite(sourceTime) && Math.abs(video.currentTime - sourceTime) > 0.05 &&
        (!Number.isFinite(video.duration) || sourceTime < video.duration)) video.currentTime = sourceTime;
      if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;
    } else if (!size.width || !size.height || !(source as HTMLImageElement).complete) {
      return;
    }
    const local = Math.max(0, time - clip.start);
    const opacity = clipProperty(clip, 'opacity', time, clip.transform.opacity) * track.opacity
      * (clip.fade_in > 0 ? Math.min(1, local / clip.fade_in) : 1)
      * (clip.fade_out > 0 ? Math.min(1, (clipLength(clip) - local) / clip.fade_out) : 1);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, upload(clip.id, source, isVideo));
    const crop = clipCrop(clip, time);
    gl.uniform4f(uniform.u_crop, crop.l, crop.t, crop.r, crop.b);
    gl.uniform1f(uniform.u_opacity, Math.max(0, opacity));
    gl.uniform1i(uniform.u_cropMask, hasAnimatedCrop(clip) ? 1 : 0);
    gl.uniform1i(uniform.u_solid, 0);
    gl.uniform1i(uniform.u_premultiplied, 0);
    transition(type, progress, role);
    geometry(quad(clip, size.width, size.height, time), buildLayerMatrix(clip, track, canvasSize, size, time), shift);
  }

  function fill(type: TransitionType, progress: number, white: boolean): void {
    gl.uniform1i(uniform.u_solid, 1);
    gl.uniform1i(uniform.u_cropMask, 0);
    gl.uniform1i(uniform.u_premultiplied, 0);
    gl.uniform1f(uniform.u_opacity, 1);
    gl.uniform4f(uniform.u_solidColor, white ? 1 : 0, white ? 1 : 0, white ? 1 : 0, 1);
    transition(type, progress, 3);
    geometry(fullQuad(), IDENTITY);
    gl.uniform1i(uniform.u_solid, 0);
  }

  function ensureTarget(width: number, height: number): void {
    const key = width + 'x' + height;
    if (targetSize === key && targetTexture && targetFramebuffer) return;
    if (targetTexture) gl.deleteTexture(targetTexture);
    if (targetFramebuffer) gl.deleteFramebuffer(targetFramebuffer);
    targetTexture = gl.createTexture();
    targetFramebuffer = gl.createFramebuffer();
    if (!targetTexture || !targetFramebuffer) throw new Error('WebGL2 transition target allocation failed');
    targetSize = key;
    gl.bindTexture(gl.TEXTURE_2D, targetTexture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.bindFramebuffer(gl.FRAMEBUFFER, targetFramebuffer);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, targetTexture, 0);
    if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error('WebGL2 transition framebuffer incomplete');
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }

  function compositeTarget(width: number, height: number): void {
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, width, height);
    gl.uniform1i(uniform.u_solid, 0);
    gl.uniform1i(uniform.u_cropMask, 0);
    gl.uniform1i(uniform.u_premultiplied, 1);
    gl.uniform1i(uniform.u_transition, 0);
    gl.uniform1f(uniform.u_opacity, 1);
    gl.uniform4f(uniform.u_crop, 0, 0, 0, 0);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, targetTexture);
    const targetQuad = new Float32Array([
      -1, 1, 0, 1, 1, 1, 1, 1, 1, -1, 1, 0,
      -1, 1, 0, 1, 1, -1, 1, 0, -1, -1, 0, 0,
    ]);
    geometry(targetQuad, IDENTITY);
    gl.uniform1i(uniform.u_premultiplied, 0);
  }

  function drawTransition(layer: TransitionLayer, time: number, doc: Doc, sources: LayerSourceLookup, size: [number, number]): void {
    const [width, height] = size;
    ensureTarget(width, height);
    gl.bindFramebuffer(gl.FRAMEBUFFER, targetFramebuffer);
    gl.viewport(0, 0, width, height);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.blendFunc(gl.ONE, gl.ONE);
    let fromShift: [number, number] = [0, 0];
    let toShift: [number, number] = [0, 0];
    if (layer.transition.type === 'slideleft') {
      fromShift = [-2 * layer.progress, 0];
      toShift = [2 * (1 - layer.progress), 0];
    } else if (layer.transition.type === 'slideright') {
      fromShift = [2 * layer.progress, 0];
      toShift = [-2 * (1 - layer.progress), 0];
    }
    drawClip(layer.from, layer.track, time, doc.canvas, sources.get(layer.from.id), layer.transition.type, layer.progress, 1, fromShift);
    drawClip(layer.to, layer.track, time, doc.canvas, sources.get(layer.to.id), layer.transition.type, layer.progress, 2, toShift);
    if (layer.transition.type === 'fadeblack' || layer.transition.type === 'fadewhite') {
      fill(layer.transition.type, layer.progress, layer.transition.type === 'fadewhite');
    }
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    compositeTarget(width, height);
  }

  return {
    render(doc, time, sources) {
      if (destroyed) return;
      const size = previewSize(canvas, doc.canvas);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.viewport(0, 0, size[0], size[1]);
      gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.clearColor(...rgba(doc.canvas.background));
      gl.clear(gl.COLOR_BUFFER_BIT);
      for (const layer of orderedLayers(doc, time)) {
        if (layer.kind === 'clip') drawClip(layer.clip, layer.track, time, doc.canvas, sources.get(layer.clipId));
        else drawTransition(layer, time, doc, sources, size);
      }
    },
    destroy() {
      if (destroyed) return;
      destroyed = true;
      for (const entry of textures.values()) gl.deleteTexture(entry.texture);
      textures.clear();
      if (targetTexture) gl.deleteTexture(targetTexture);
      if (targetFramebuffer) gl.deleteFramebuffer(targetFramebuffer);
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
    },
  };
}

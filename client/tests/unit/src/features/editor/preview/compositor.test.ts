import { describe, expect, it, vi } from 'vitest';

import { buildLayerMatrix, orderedLayers } from '@/features/editor/preview/compositor';
import { createCompositor } from '@/features/editor/preview/webgl';
import type { Canvas, Doc, Transform, VideoTrack, VisualClip } from '@/features/editor/model/types';

const canvas: Canvas = { width: 800, height: 600, fps: 30, background: '#000000' };

function visualClip(id: string, track: string, start = 0, values: Partial<Transform> = {}): VisualClip {
  return {
    id,
    track,
    src: `${id}.png`,
    src_in: 0,
    src_out: 4,
    start,
    fade_in: 0,
    fade_out: 0,
    media: 'image',
    transform: {
      x: 0,
      y: 0,
      scale_x: 1,
      scale_y: 1,
      rotation: 0,
      opacity: 1,
      crop: { l: 0, t: 0, r: 0, b: 0 },
      anchor_x: 0.5,
      anchor_y: 0.5,
      ...values,
    },
    keyframes: {},
  };
}

function videoTrack(id: string, values: Partial<VideoTrack> = {}): VideoTrack {
  return { id, kind: 'video', name: id, opacity: 1, hidden: false, locked: false, ...values };
}

function project(tracks: VideoTrack[], clips: VisualClip[], transitions: Doc['transitions'] = []): Doc {
  return { version: 2, name: 'preview', sample_rate: 48000, canvas, tracks, clips, markers: [], transitions };
}

function point(matrix: Float32Array, x: number, y: number): [number, number] {
  return [matrix[0] * x + matrix[3] * y + matrix[6], matrix[1] * x + matrix[4] * y + matrix[7]];
}

describe('compositor WebGL2', () => {
  it('aplica crop, rotación, escala, posición y keyframes en coordenadas del lienzo', () => {
    const clip = visualClip('logo', 'v1', 0, {
      x: 100,
      y: -50,
      scale_x: 2,
      scale_y: 0.5,
      rotation: 90,
      crop: { l: 0.1, t: 0.2, r: 0.1, b: 0.2 },
    });
    clip.keyframes = { x: [{ t: 0, value: 100, ease: 'linear' }, { t: 4, value: 300, ease: 'linear' }] };

    const matrix = buildLayerMatrix(clip, videoTrack('v1'), canvas, { width: 200, height: 100 }, 2);

    expect(point(matrix, 20, 20)[0]).toBeCloseTo(0.65, 6);
    expect(point(matrix, 20, 20)[1]).toBeCloseTo(0.3, 6);
    expect(point(matrix, 180, 80)[0]).toBeCloseTo(0.35, 6);
    expect(point(matrix, 180, 80)[1]).toBeCloseTo(1 / 30, 6);
  });

  it('ordena capas de abajo hacia arriba, omite pistas ocultas y agrupa la transición activa', () => {
    const a = visualClip('a', 'low', 0);
    const b = visualClip('b', 'low', 3);
    const upper = visualClip('upper', 'high', 3);
    const doc = project(
      [videoTrack('low'), videoTrack('hidden', { hidden: true }), videoTrack('high')],
      [upper, b, a],
      [{ id: 'fade', track: 'low', a: 'a', b: 'b', type: 'fade', duration: 1 }],
    );

    expect(orderedLayers(doc, 3.5).map((layer) => layer.kind)).toEqual(['transition', 'clip']);
    expect(orderedLayers(doc, 3.5)[0]).toMatchObject({ clipIds: ['a', 'b'], progress: 0.5 });
    expect(orderedLayers(doc, 3.5)[1]).toMatchObject({ clipId: 'upper', trackId: 'high' });
  });

  it('emite un draw por capa activa usando el contexto WebGL simulado', () => {
    const draws = vi.fn();
    const uniform = (name: string) => ({ name }) as unknown as WebGLUniformLocation;
    const gl = {
      VERTEX_SHADER: 35633,
      FRAGMENT_SHADER: 35632,
      COMPILE_STATUS: 35713,
      LINK_STATUS: 35714,
      ARRAY_BUFFER: 34962,
      FRAMEBUFFER: 36160,
      FRAMEBUFFER_COMPLETE: 36053,
      COLOR_ATTACHMENT0: 36064,
      RGBA8: 32856,
      ELEMENT_ARRAY_BUFFER: 34963,
      STATIC_DRAW: 35044,
      DYNAMIC_DRAW: 35048,
      FLOAT: 5126,
      TEXTURE_2D: 3553,
      TEXTURE0: 33984,
      TEXTURE1: 33985,
      TEXTURE2: 33986,
      TEXTURE_3D: 32879,
      RGBA: 6408,
      RGB: 6407,
      RGB8: 32849,
      UNSIGNED_BYTE: 5121,
      TEXTURE_MIN_FILTER: 10241,
      TEXTURE_MAG_FILTER: 10240,
      LINEAR: 9729,
      TEXTURE_WRAP_S: 10242,
      TEXTURE_WRAP_T: 10243,
      TEXTURE_WRAP_R: 32882,
      CLAMP_TO_EDGE: 33071,
      NEAREST: 9728,
      UNPACK_FLIP_Y_WEBGL: 37440,
      TRIANGLES: 4,
      BLEND: 3042,
      ONE: 1,
      ONE_MINUS_SRC_ALPHA: 771,
      COLOR_BUFFER_BIT: 16384,
      createShader: vi.fn(() => ({})),
      shaderSource: vi.fn(),
      compileShader: vi.fn(),
      getShaderParameter: vi.fn(() => true),
      getShaderInfoLog: vi.fn(() => ''),
      createProgram: vi.fn(() => ({})),
      attachShader: vi.fn(),
      linkProgram: vi.fn(),
      getProgramParameter: vi.fn(() => true),
      getProgramInfoLog: vi.fn(() => ''),
      getAttribLocation: vi.fn((_program: WebGLProgram, name: string) => (name === 'a_position' ? 0 : 1)),
      getUniformLocation: vi.fn((_program: WebGLProgram, name: string) => uniform(name)),
      createBuffer: vi.fn(() => ({})),
      createTexture: vi.fn(() => ({})),
      createFramebuffer: vi.fn(() => ({})),
      bindBuffer: vi.fn(),
      bufferData: vi.fn(),
      bindTexture: vi.fn(),
      texParameteri: vi.fn(),
      pixelStorei: vi.fn(),
      texImage2D: vi.fn(),
      texImage3D: vi.fn(),
      copyTexImage2D: vi.fn(),
      activeTexture: vi.fn(),
      enableVertexAttribArray: vi.fn(),
      vertexAttribPointer: vi.fn(),
      useProgram: vi.fn(),
      uniformMatrix3fv: vi.fn(),
      uniform1f: vi.fn(),
      uniform1i: vi.fn(),
      uniform2f: vi.fn(),
      uniform4f: vi.fn(),
      viewport: vi.fn(),
      bindFramebuffer: vi.fn(),
      framebufferTexture2D: vi.fn(),
      checkFramebufferStatus: vi.fn(() => 36053),
      clearColor: vi.fn(),
      clear: vi.fn(),
      enable: vi.fn(),
      disable: vi.fn(),
      blendFunc: vi.fn(),
      drawArrays: draws,
      deleteBuffer: vi.fn(),
      deleteTexture: vi.fn(),
      deleteFramebuffer: vi.fn(),
      deleteProgram: vi.fn(),
      deleteShader: vi.fn(),
      drawingBufferWidth: 64,
      drawingBufferHeight: 64,
    } as unknown as WebGL2RenderingContext;
    const element = document.createElement('canvas');
    vi.spyOn(element, 'getContext').mockReturnValue(gl);
    const doc = project([videoTrack('low'), videoTrack('high')], [visualClip('low', 'low'), visualClip('high', 'high')]);
    const source = { width: 16, height: 16, complete: true } as HTMLImageElement;
    const compositor = createCompositor(element);

    compositor.render(doc, 1, new Map([['low', source], ['high', source]]));

    expect(draws).toHaveBeenCalledTimes(2);
    const effectClip = { ...visualClip('effects', 'high'), blend_mode: 'multiply' as const };
    effectClip.color = {
      brightness: 0.1, contrast: 1.2, saturation: 0.9, gamma: 1.1,
      lut: 'media/luts/lut-' + 'a'.repeat(64) + '.cube',
    };
    effectClip.chroma = { color: '#00ff00', similarity: 0.2, blend: 0.1, despill: true };
    const lut = { size: 2, data: new Uint8Array(24), domainMin: [0, 0, 0] as [number, number, number], domainMax: [1, 1, 1] as [number, number, number] };
    const effectSources = { get: (id: string) => id === 'effects' ? source : undefined, getLut: () => lut };
    compositor.render(project([videoTrack('high')], [effectClip]), 1, effectSources);
    expect(gl.texImage3D).toHaveBeenCalledOnce();
    expect(gl.copyTexImage2D).toHaveBeenCalledOnce();
    expect(gl.disable).toHaveBeenCalledWith(gl.BLEND);
    expect(gl.uniform1i).toHaveBeenCalledWith(expect.objectContaining({ name: 'u_hasChroma' }), 1);
    expect(gl.uniform1i).toHaveBeenCalledWith(expect.objectContaining({ name: 'u_blendMode' }), 1);
    const transitionDoc = project(
      [videoTrack('v1')],
      [visualClip('a', 'v1'), visualClip('b', 'v1', 3)],
      [{ id: 'x', track: 'v1', a: 'a', b: 'b', type: 'fade', duration: 1 }],
    );
    const transitionSources = new Map([['a', source], ['b', source]]);
    const transitionTypes = ['fade', 'fadeblack', 'fadewhite', 'wipeleft', 'wiperight', 'slideleft', 'slideright', 'circleopen'] as const;
    for (const type of transitionTypes) {
      transitionDoc.transitions[0].type = type;
      compositor.render(transitionDoc, 3.5, transitionSources);
    }
    const afterTransitions = draws.mock.calls.length;
    const missingSourceDoc = project([videoTrack('v1')], [visualClip('missing', 'v1')]);
    compositor.render(missingSourceDoc, 1, new Map());
    expect(draws.mock.calls.length).toBe(afterTransitions);

    const video = document.createElement('video');
    let currentTime = 0;
    Object.defineProperties(video, {
      videoWidth: { value: 16 },
      videoHeight: { value: 16 },
      duration: { value: 5 },
      readyState: { value: 2 },
      currentTime: { get: () => currentTime, set: (value: number) => { currentTime = value; } },
    });
    const videoClip = { ...visualClip('video', 'v1'), media: 'video' as const, speed: 2 };
    const videoDoc = project([videoTrack('v1')], [videoClip]);
    compositor.render(videoDoc, 1, new Map([['video', video]]));
    expect(currentTime).toBe(2);
    expect(video.playbackRate).toBe(2);

    compositor.destroy();
    compositor.destroy();
    compositor.render(doc, 1, new Map([['low', source], ['high', source]]));
  });
});

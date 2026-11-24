import { describe, expect, it, vi } from 'vitest';

import { createCompositor } from '@/features/editor/preview/webgl';

type InitFaults = {
  shaderAllocation?: boolean;
  shaderCompiled?: boolean;
  programAllocation?: boolean;
  programLinked?: boolean;
  bufferAllocation?: boolean;
};

function context(faults: InitFaults = {}): WebGL2RenderingContext {
  return {
    VERTEX_SHADER: 35633,
    FRAGMENT_SHADER: 35632,
    COMPILE_STATUS: 35713,
    LINK_STATUS: 35714,
    ARRAY_BUFFER: 34962,
    STATIC_DRAW: 35044,
    DYNAMIC_DRAW: 35048,
    FLOAT: 5126,
    BLEND: 3042,
    ONE: 1,
    ONE_MINUS_SRC_ALPHA: 771,
    UNPACK_FLIP_Y_WEBGL: 37440,
    TEXTURE0: 33984,
    TEXTURE1: 33985,
    TEXTURE2: 33986,
    TEXTURE_2D: 3553,
    TEXTURE_MIN_FILTER: 10241,
    TEXTURE_MAG_FILTER: 10240,
    TEXTURE_WRAP_S: 10242,
    TEXTURE_WRAP_T: 10243,
    LINEAR: 9729,
    NEAREST: 9728,
    CLAMP_TO_EDGE: 33071,
    createTexture: vi.fn(() => ({})),
    activeTexture: vi.fn(),
    bindTexture: vi.fn(),
    texParameteri: vi.fn(),
    createShader: vi.fn(() => faults.shaderAllocation === false ? null : ({})),
    shaderSource: vi.fn(),
    compileShader: vi.fn(),
    getShaderParameter: vi.fn(() => faults.shaderCompiled !== false),
    getShaderInfoLog: vi.fn(() => ''),
    createProgram: vi.fn(() => faults.programAllocation === false ? null : ({})),
    attachShader: vi.fn(),
    linkProgram: vi.fn(),
    getProgramParameter: vi.fn(() => faults.programLinked !== false),
    getProgramInfoLog: vi.fn(() => ''),
    getAttribLocation: vi.fn(() => 0),
    getUniformLocation: vi.fn(() => ({})),
    createBuffer: vi.fn(() => faults.bufferAllocation === false ? null : ({})),
    useProgram: vi.fn(),
    bindBuffer: vi.fn(),
    enableVertexAttribArray: vi.fn(),
    vertexAttribPointer: vi.fn(),
    pixelStorei: vi.fn(),
    enable: vi.fn(),
    blendFunc: vi.fn(),
    uniform1i: vi.fn(),
    deleteTexture: vi.fn(),
    deleteBuffer: vi.fn(),
    deleteProgram: vi.fn(),
  } as unknown as WebGL2RenderingContext;
}

function canvasFor(gl: WebGL2RenderingContext): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  vi.spyOn(canvas, 'getContext').mockReturnValue(gl);
  return canvas;
}

describe('inicialización WebGL2', () => {
  it('informa cuando el navegador no puede crear un contexto WebGL2', () => {
    const canvas = document.createElement('canvas');
    vi.spyOn(canvas, 'getContext').mockReturnValue(null);

    expect(() => createCompositor(canvas)).toThrow('WebGL2 unavailable');
  });

  it('propaga fallos al asignar, compilar y enlazar recursos', () => {
    const faults: Array<[InitFaults, string]> = [
      [{ shaderAllocation: false }, 'WebGL2 shader allocation failed'],
      [{ shaderCompiled: false }, 'WebGL2 shader compilation failed'],
      [{ programAllocation: false }, 'WebGL2 program allocation failed'],
      [{ programLinked: false }, 'WebGL2 program link failed'],
      [{ bufferAllocation: false }, 'WebGL2 buffer allocation failed'],
    ];

    for (const [options, message] of faults) {
      expect(() => createCompositor(canvasFor(context(options)))).toThrow(message);
    }
  });

  it('libera los recursos base antes del primer cuadro', () => {
    const gl = context();
    const compositor = createCompositor(canvasFor(gl));

    compositor.destroy();

    expect(gl.deleteBuffer).toHaveBeenCalledTimes(1);
    expect(gl.deleteProgram).toHaveBeenCalledTimes(1);
  });
});

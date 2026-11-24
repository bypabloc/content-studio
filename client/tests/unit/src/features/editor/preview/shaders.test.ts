import { describe, expect, it, vi } from 'vitest';

import { createProgram, FRAGMENT_SHADER, getUniforms, VERTEX_SHADER } from '@/features/editor/preview/shaders';

function shaderContext(overrides: Record<string, unknown> = {}): WebGL2RenderingContext {
  return {
    VERTEX_SHADER: 35633,
    FRAGMENT_SHADER: 35632,
    COMPILE_STATUS: 35713,
    LINK_STATUS: 35714,
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
    getUniformLocation: vi.fn((_program: WebGLProgram, name: string) => ({ name } as unknown as WebGLUniformLocation)),
    ...overrides,
  } as unknown as WebGL2RenderingContext;
}

describe('shaders del compositor', () => {
  it('mapea posiciones transformadas y recorta coordenadas de textura en WebGL2', () => {
    expect(VERTEX_SHADER).toContain('#version 300 es');
    expect(VERTEX_SHADER).toContain('u_matrix');
    expect(VERTEX_SHADER).toContain('a_texCoord');
    expect(FRAGMENT_SHADER).toContain('u_crop');
    expect(FRAGMENT_SHADER).toContain('u_opacity');
  });

  it('devuelve color premultiplicado y calcula la máscara de transición sobre el lienzo', () => {
    expect(FRAGMENT_SHADER).toContain('precision highp sampler3D;');
    expect(FRAGMENT_SHADER).toContain('corrected * alpha');
    expect(FRAGMENT_SHADER).toContain('u_progress');
    expect(FRAGMENT_SHADER).toContain('u_transition');
  });

  it('compila los shaders y obtiene los uniformes del programa', () => {
    const gl = shaderContext();
    const program = createProgram(gl);

    expect(gl.attachShader).toHaveBeenCalledTimes(2);
    expect(getUniforms(gl, program).u_lutSize).toEqual({ name: 'u_lutSize' });
  });

  it('informa fallos de asignación, compilación y enlace', () => {
    expect(() => createProgram(shaderContext({ createShader: vi.fn(() => null) }))).toThrow('shader allocation failed');
    expect(() => createProgram(shaderContext({ createProgram: vi.fn(() => null) }))).toThrow('program allocation failed');
    expect(() => createProgram(shaderContext({ getShaderParameter: vi.fn(() => false) }))).toThrow('shader compilation failed');
    expect(() => createProgram(shaderContext({ getProgramParameter: vi.fn(() => false) }))).toThrow('program link failed');
  });
});

import { describe, expect, it } from 'vitest';

import { FRAGMENT_SHADER, VERTEX_SHADER } from '@/features/editor/preview/shaders';

describe('shaders del compositor', () => {
  it('mapea posiciones transformadas y recorta coordenadas de textura en WebGL2', () => {
    expect(VERTEX_SHADER).toContain('#version 300 es');
    expect(VERTEX_SHADER).toContain('u_matrix');
    expect(VERTEX_SHADER).toContain('a_texCoord');
    expect(FRAGMENT_SHADER).toContain('u_crop');
    expect(FRAGMENT_SHADER).toContain('u_opacity');
  });

  it('devuelve color premultiplicado y calcula la máscara de transición sobre el lienzo', () => {
    expect(FRAGMENT_SHADER).toContain('color.rgb * alpha');
    expect(FRAGMENT_SHADER).toContain('u_progress');
    expect(FRAGMENT_SHADER).toContain('u_transition');
  });
});

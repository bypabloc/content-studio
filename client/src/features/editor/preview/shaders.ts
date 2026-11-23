/** Uniformes que usan los shaders del compositor y de sus efectos. */
export type Uniforms = Record<string, WebGLUniformLocation | null>;

function compile(gl: WebGL2RenderingContext, type: number, source: string): WebGLShader {
  const shader = gl.createShader(type);
  if (!shader) throw new Error('WebGL2 shader allocation failed');
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) || 'WebGL2 shader compilation failed'); // i18n-ignore: mensaje interno de WebGL sin salida directa en la interfaz
  return shader;
}

/** Compila y enlaza los shaders del compositor. */
export function createProgram(gl: WebGL2RenderingContext): WebGLProgram {
  const program = gl.createProgram();
  if (!program) throw new Error('WebGL2 program allocation failed');
  gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERTEX_SHADER));
  gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER));
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program) || 'WebGL2 program link failed'); // i18n-ignore: mensaje interno de WebGL sin salida directa en la interfaz
  return program;
}

/** Busca los uniformes por nombre para compartirlos con el compositor y sus efectos. */
export function getUniforms(gl: WebGL2RenderingContext, program: WebGLProgram): Uniforms {
  const names = [
    'u_matrix', 'u_shift', 'u_texture', 'u_crop', 'u_opacity', 'u_progress', 'u_transition',
    'u_role', 'u_cropMask', 'u_solid', 'u_solidColor', 'u_premultiplied', 'u_background', 'u_lut',
    'u_color', 'u_chromaColor', 'u_chromaBlend', 'u_lutDomainMin', 'u_lutDomainMax', 'u_hasChroma',
    'u_hasLut', 'u_despill', 'u_blendMode', 'u_lutSize',
  ];
  return Object.fromEntries(names.map((name) => [name, gl.getUniformLocation(program, name)]));
}

/** Shader de capas transformadas sobre un lienzo WebGL2. */
// cspell:ignore highp: GLSL precision qualifier.
export const VERTEX_SHADER = `#version 300 es
in vec2 a_position;
in vec2 a_texCoord;
uniform mat3 u_matrix;
uniform vec2 u_shift;
out vec2 v_texCoord;
out vec2 v_canvas;
void main() {
  vec3 point = u_matrix * vec3(a_position, 1.0);
  point.xy += u_shift;
  gl_Position = vec4(point.xy, 0.0, 1.0);
  v_texCoord = a_texCoord;
  v_canvas = vec2((point.x + 1.0) * 0.5, (1.0 - point.y) * 0.5);
}`;

export const FRAGMENT_SHADER = `#version 300 es
precision highp float;
precision highp sampler3D;
in vec2 v_texCoord;
in vec2 v_canvas;
uniform sampler2D u_texture;
uniform sampler2D u_background;
uniform sampler3D u_lut;
uniform vec4 u_crop;
uniform float u_opacity;
uniform float u_progress;
uniform float u_chromaBlend;
uniform vec4 u_color;
uniform vec4 u_chromaColor;
uniform vec4 u_lutDomainMin;
uniform vec4 u_lutDomainMax;
uniform float u_lutSize;
uniform int u_transition;
uniform int u_role;
uniform int u_cropMask;
uniform int u_solid;
uniform int u_premultiplied;
uniform int u_hasChroma;
uniform int u_hasLut;
uniform int u_despill;
uniform int u_blendMode;
uniform vec4 u_solidColor;
out vec4 outColor;
float transitionWeight() {
  float p = clamp(u_progress, 0.0, 1.0);
  if (u_transition == 0) return 1.0;
  if (u_transition == 1) return u_role == 1 ? 1.0 - p : p;
  if (u_transition == 2 || u_transition == 3) {
    float fadeOut = smoothstep(0.8, 1.0, p);
    float fadeIn = smoothstep(0.2, 1.0, p);
    float first = (1.0 - fadeOut) * (1.0 - p);
    float second = fadeIn * p;
    if (u_role == 1) return first;
    if (u_role == 2) return second;
    return 1.0 - first - second;
  }
  if (u_transition == 4) return u_role == 2 ? 1.0 - step(v_canvas.x, p) : step(v_canvas.x, p);
  if (u_transition == 5) return u_role == 2 ? 1.0 - step(1.0 - p, v_canvas.x) : step(1.0 - p, v_canvas.x);
  if (u_transition == 6 || u_transition == 7) return 1.0;
  if (u_transition == 8) {
    float reveal = smoothstep(0.0, 1.0, distance(v_canvas, vec2(0.5)) * 1.41421356 + (p - 0.5) * 3.0);
    return u_role == 2 ? reveal : 1.0 - reveal;
  }
  return 1.0;
}
vec2 chromaUv(vec3 color) {
  float luma = dot(color, vec3(0.299, 0.587, 0.114));
  return vec2((color.b - luma) * 0.565 + 0.5, (color.r - luma) * 0.713 + 0.5);
}
vec3 blendColor(vec3 source, vec3 destination) {
  if (u_blendMode == 1) return source * destination;
  if (u_blendMode == 2) return source + destination - source * destination;
  if (u_blendMode == 3) return mix(2.0 * source * destination, 1.0 - 2.0 * (1.0 - source) * (1.0 - destination), step(vec3(0.5), destination));
  if (u_blendMode == 4) return min(source, destination);
  if (u_blendMode == 5) return max(source, destination);
  if (u_blendMode == 6) return min(source + destination, vec3(1.0));
  if (u_blendMode == 7) return abs(destination - source);
  return source;
}
void main() {
  if (u_solid == 1) {
    float factor = transitionWeight();
    float alpha = u_solidColor.a * factor * u_opacity;
    outColor = vec4(u_solidColor.rgb * alpha, alpha);
    return;
  }
  if (u_cropMask == 1 && (v_texCoord.x < u_crop.x || v_texCoord.y < u_crop.y || v_texCoord.x >= 1.0 - u_crop.z || v_texCoord.y >= 1.0 - u_crop.w)) discard;
  vec4 color = texture(u_texture, v_texCoord);
  if (u_premultiplied == 1) {
    outColor = color * u_opacity;
    return;
  }
  float luma = dot(color.rgb, vec3(0.299, 0.587, 0.114));
  vec3 corrected = (vec3(luma) + (color.rgb - vec3(luma)) * u_color.z - 0.5) * u_color.y + 0.5 + u_color.x;
  corrected = pow(max(corrected, vec3(0.0)), vec3(1.0 / max(u_color.w, 0.1)));
  if (u_hasLut == 1) {
    vec3 lookup = clamp((corrected - u_lutDomainMin.rgb) / (u_lutDomainMax.rgb - u_lutDomainMin.rgb), 0.0, 1.0);
    lookup = (lookup * (u_lutSize - 1.0) + 0.5) / u_lutSize;
    corrected = texture(u_lut, lookup).rgb;
  }
  float alpha = color.a * u_opacity * transitionWeight();
  if (u_hasChroma == 1) {
    float distanceToKey = distance(chromaUv(corrected), chromaUv(u_chromaColor.rgb));
    float keep = smoothstep(u_chromaColor.a, u_chromaColor.a + max(u_chromaBlend, 0.00001), distanceToKey);
    if (u_despill == 1) corrected.g = mix(min(corrected.g, max(corrected.r, corrected.b)), corrected.g, keep);
    if (u_despill == 2) corrected.b = mix(min(corrected.b, max(corrected.r, corrected.g)), corrected.b, keep);
    alpha *= keep;
  }
  if (u_blendMode != 0) {
    vec4 destination = texture(u_background, vec2(v_canvas.x, 1.0 - v_canvas.y));
    vec3 destinationColor = destination.a > 0.0 ? destination.rgb / destination.a : vec3(0.0);
    vec3 blended = blendColor(corrected, destinationColor);
    float outputAlpha = alpha + destination.a - alpha * destination.a;
    vec3 outputColor = (1.0 - alpha) * destination.rgb + (1.0 - destination.a) * corrected * alpha + alpha * destination.a * blended;
    outColor = vec4(outputColor, outputAlpha);
    return;
  }
  outColor = vec4(corrected * alpha, alpha);
}`;

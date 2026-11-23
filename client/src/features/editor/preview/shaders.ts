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
in vec2 v_texCoord;
in vec2 v_canvas;
uniform sampler2D u_texture;
uniform vec4 u_crop;
uniform float u_opacity;
uniform float u_progress;
uniform int u_transition;
uniform int u_role;
uniform int u_cropMask;
uniform int u_solid;
uniform int u_premultiplied;
uniform vec4 u_solidColor;
out vec4 outColor;
float transitionWeight() {
  float p = clamp(u_progress, 0.0, 1.0);
  if (u_transition == 0) return 1.0;
  if (u_transition == 1) return u_role == 1 ? 1.0 - p : p;
  if (u_transition == 2 || u_transition == 3) {
    float first = max(0.0, 1.0 - 2.0 * p);
    float second = max(0.0, 2.0 * p - 1.0);
    if (u_role == 1) return first;
    if (u_role == 2) return second;
    return 1.0 - first - second;
  }
  if (u_transition == 4) return u_role == 2 ? step(v_canvas.x, p) : 1.0 - step(v_canvas.x, p);
  if (u_transition == 5) return u_role == 2 ? step(1.0 - p, v_canvas.x) : 1.0 - step(1.0 - p, v_canvas.x);
  if (u_transition == 6 || u_transition == 7) return 1.0;
  if (u_transition == 8) {
    float inside = step(distance(v_canvas, vec2(0.5)), p * 0.70710678);
    return u_role == 2 ? inside : 1.0 - inside;
  }
  return 1.0;
}
void main() {
  if (u_solid == 1) {
    float factor = transitionWeight();
    float alpha = u_solidColor.a * factor;
    outColor = vec4(u_solidColor.rgb * alpha, alpha);
    return;
  }
  if (u_cropMask == 1 && (v_texCoord.x < u_crop.x || v_texCoord.y < u_crop.y || v_texCoord.x >= 1.0 - u_crop.z || v_texCoord.y >= 1.0 - u_crop.w)) discard;
  vec4 color = texture(u_texture, v_texCoord);
  if (u_premultiplied == 1) {
    outColor = color * u_opacity;
    return;
  }
  float alpha = color.a * u_opacity * transitionWeight();
  outColor = vec4(color.rgb * alpha, alpha);
}`;

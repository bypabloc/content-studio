import type { TextStyle } from '../model/types';

export type RasterizedText = { blob: Blob; hash: string; width: number; height: number };

function textLines(context: OffscreenCanvasRenderingContext2D, content: string, maxWidth: number): string[] {
  const result: string[] = [];
  for (const paragraph of content.split(/\r?\n/)) {
    let line = '';
    for (const word of paragraph.trim().split(/\s+/).filter(Boolean)) {
      const next = line ? `${line} ${word}` : word;
      if (line && context.measureText(next).width > maxWidth) {
        result.push(line);
        line = word;
      } else {
        line = next;
      }
    }
    result.push(line);
  }
  return result.length ? result : [''];
}

function fontFamily(family: string): string {
  return `"${family.replaceAll('\\', '\\\\').replaceAll('"', '\\"')}"`;
}

async function hashBlob(blob: Blob): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

/** Convierte el estilo de texto del editor en una imagen PNG con transparencia. */
export async function rasterizeText(style: TextStyle): Promise<RasterizedText> {
  const canvas = new OffscreenCanvas(1, 1);
  const measure = canvas.getContext('2d', { alpha: true });
  if (!measure) throw new Error('No se pudo crear el contexto de texto.');
  measure.font = `${style.weight} ${style.size}px ${fontFamily(style.font)}`;
  const lines = textLines(measure, style.content, style.max_width);
  const textWidth = Math.max(1, ...lines.map((line) => measure.measureText(line).width));
  const padding = Math.ceil(Math.max(
    style.box?.padding ?? 0,
    style.stroke.width,
    style.shadow.blur + Math.max(Math.abs(style.shadow.x), Math.abs(style.shadow.y)),
  ));
  const lineHeight = style.size * style.line_height;
  const width = Math.ceil(textWidth + padding * 2);
  const height = Math.ceil(lines.length * lineHeight + padding * 2);
  const output = new OffscreenCanvas(width, height);
  const context = output.getContext('2d', { alpha: true });
  if (!context) throw new Error('No se pudo crear el contexto de texto.');
  context.clearRect(0, 0, width, height);
  if (style.box) {
    context.fillStyle = style.box.color;
    context.beginPath();
    context.roundRect(0, 0, width, height, style.box.radius);
    context.fill();
  }
  context.font = `${style.weight} ${style.size}px ${fontFamily(style.font)}`;
  context.textAlign = style.align;
  context.textBaseline = 'alphabetic';
  context.lineWidth = style.stroke.width * 2;
  context.strokeStyle = style.stroke.color;
  context.fillStyle = style.color;
  context.shadowColor = style.shadow.color;
  context.shadowBlur = style.shadow.blur;
  context.shadowOffsetX = style.shadow.x;
  context.shadowOffsetY = style.shadow.y;
  const x = style.align === 'left' ? padding : style.align === 'right' ? width - padding : width / 2;
  lines.forEach((line, index) => {
    const y = padding + style.size + index * lineHeight;
    context.strokeText(line, x, y);
    context.fillText(line, x, y);
  });
  const blob = await output.convertToBlob({ type: 'image/png' });
  return { blob, hash: await hashBlob(blob), width, height };
}

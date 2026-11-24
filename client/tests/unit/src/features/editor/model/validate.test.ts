// Espejo de server/tests/unit/src/content_studio/editor/test_project.py: validación y duración con las mismas fixtures.
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

import { duration, validate } from '@/features/editor/model/validate';
import type { Doc, TextClip } from '@/features/editor/model/types';

const FIXTURES = join(process.cwd(), '..', 'server', 'tests', 'fixtures', 'editor');
const load = (name: string) => JSON.parse(readFileSync(join(FIXTURES, name), 'utf-8'));
const INVALID = readdirSync(FIXTURES)
  .filter((name) => name.startsWith('invalid-'))
  .sort();

function validTextProject(): Doc {
  const title: TextClip = {
    id: 'title', track: 'video', src: 'media/text-title.png', raster: 'media/text-title.png', media: 'text',
    text: {
      content: 'Title', font: 'Arial', weight: 700, size: 48, color: '#ffffff',
      stroke: { width: 2, color: '#000000' }, shadow: { x: 0, y: 2, blur: 4, color: '#000000' },
      box: { color: '#000000aa', padding: 8, radius: 4 }, align: 'center', line_height: 1.2, max_width: 800,
    },
    src_in: 0, src_out: 5, start: 0, fade_in: 0, fade_out: 0, speed: 1,
    transform: {
      x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
      crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
    },
    keyframes: {},
    color: { brightness: 0, contrast: 1, saturation: 1, gamma: 1, lut: 'media/look.cube' },
    chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1 },
    blend_mode: 'normal',
  };
  return {
    version: 3, name: 'Text', sample_rate: 48000,
    canvas: { width: 1280, height: 720, fps: 30, background: '#000000' },
    tracks: [
      { id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false },
      { id: 'subtitles', kind: 'subtitles', name: 'Subtitles', subtitles_project: 'subtitles/project.json', locked: false },
    ],
    clips: [title], markers: [], transitions: [],
  };
}

describe('validación del proyecto (AC-1)', () => {
  it.each(INVALID)('%s devuelve exactamente sus códigos de error', (name) => {
    const fixture = load(name);

    const codes = validate(fixture.doc as Doc).map((error) => error.code).sort();

    expect(codes).toEqual([...fixture.errors].sort());
  });

  it('acepta el documento de una fixture válida', () => {
    expect(validate(load('ops-move-sin-pisar.json').doc as Doc)).toEqual([]);
  });

  it('acepta un proyecto visual v2 con keyframes, transición y audio enlazado', () => {
    expect(validate(load('valid-visual-v2.json').doc as Doc)).toEqual([]);
  });

  it('la duración es el final del clip que más tarde termina; sin clips, 0', () => {
    const doc = load('ops-delete-sin-ripple.json').doc as Doc;

    expect(duration(doc)).toBe(12);
    expect(duration({ ...doc, clips: [] })).toBe(0);
  });

  it('rechaza velocidades fuera del rango del proyecto v3', () => {
    const doc = structuredClone(load('valid-visual-v2.json').doc);
    doc.version = 3;
    for (const clip of doc.clips) {
      clip.speed = 1;
      if ('media' in clip) {
        clip.color = { brightness: 0, contrast: 1, saturation: 1, gamma: 1 };
        clip.blend_mode = 'normal';
      }
    }
    doc.clips[0].speed = 4.01;

    expect(validate(doc as Doc)).toEqual([{ code: 'bad_speed', id: doc.clips[0].id }]);
  });

  it('acepta un clip de texto v3 con efectos y un raster dentro del proyecto', () => {
    expect(validate(validTextProject())).toEqual([]);
  });

  it.each([
    ['texto no es objeto', (clip: TextClip) => { clip.text = null as unknown as TextClip['text']; }],
    ['ruta raster insegura', (clip: TextClip) => { clip.raster = 'media/../outside.png'; }],
    ['contenido no textual', (clip: TextClip) => { clip.text.content = 42 as unknown as string; }],
    ['tamaño no positivo', (clip: TextClip) => { clip.text.size = 0; }],
    ['alineación inválida', (clip: TextClip) => { clip.text.align = 'justify' as TextClip['text']['align']; }],
    ['contorno inválido', (clip: TextClip) => { clip.text.stroke = null as unknown as TextClip['text']['stroke']; }],
    ['sombra inválida', (clip: TextClip) => { clip.text.shadow = null as unknown as TextClip['text']['shadow']; }],
    ['desenfoque de sombra negativo', (clip: TextClip) => { clip.text.shadow.blur = -1; }],
    ['caja inválida', (clip: TextClip) => { clip.text.box = { color: '#000', padding: -1, radius: 0 }; }],
    ['color no es objeto', (clip: TextClip) => { clip.color = null as unknown as TextClip['color']; }],
    ['LUT no textual', (clip: TextClip) => { clip.color!.lut = 4 as unknown as string; }],
    ['croma no es objeto', (clip: TextClip) => { clip.chroma = null as unknown as TextClip['chroma']; }],
  ])('rechaza efectos inválidos: %s', (_name, change) => {
    const doc = validTextProject();
    change(doc.clips[0] as TextClip);

    expect(validate(doc).some((error) => error.code === 'bad_text' || error.code === 'bad_color' || error.code === 'bad_chroma')).toBe(true);
  });
});

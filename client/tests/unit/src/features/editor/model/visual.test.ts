import { describe, expect, it } from 'vitest';

import { addTransitionAtCut, moveKeyframe, resizeTransition, setKeyframeEase, toggleKeyframe, writeVisualValue } from '@/features/editor/model/visual';
import type { Doc, VisualClip } from '@/features/editor/model/types';

function clip(id: string, start: number, src: string): VisualClip {
  return {
    id, track: 'video', src, src_in: 0, src_out: 4, start, fade_in: 0, fade_out: 0, media: 'image',
    transform: { x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
      crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5 },
    keyframes: {},
  };
}

function document(): Doc {
  return {
    version: 2, name: 'visual', sample_rate: 48000,
    canvas: { width: 1280, height: 720, fps: 30, background: '#000000' },
    tracks: [{ id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false }],
    clips: [clip('a', 0, 'a.png'), clip('b', 4, 'b.png')], markers: [], transitions: [],
  };
}

describe('edicion de clips visuales', () => {
  it('actualiza el valor base de una propiedad sin keyframes', () => {
    const source = document();

    const next = writeVisualValue(source, 'a', 'x', 1, 160);

    expect((next.clips[0] as VisualClip).transform.x).toBe(160);
    expect((next.clips[0] as VisualClip).keyframes).toEqual({});
    expect((source.clips[0] as VisualClip).transform.x).toBe(0);
  });

  it('inserta o alterna un keyframe con el valor interpolado del cabezal', () => {
    const source = document();
    const clipA = source.clips[0] as VisualClip;
    clipA.keyframes.x = [
      { t: 0, value: 0, ease: 'linear' },
      { t: 4, value: 100, ease: 'linear' },
    ];

    const inserted = toggleKeyframe(source, 'a', 'x', 2);
    expect((inserted.clips[0] as VisualClip).keyframes.x).toEqual([
      { t: 0, value: 0, ease: 'linear' },
      { t: 2, value: 50, ease: 'linear' },
      { t: 4, value: 100, ease: 'linear' },
    ]);

    const removed = toggleKeyframe(inserted, 'a', 'x', 2);
    expect((removed.clips[0] as VisualClip).keyframes.x).toHaveLength(2);
  });

  it('escribe en el cabezal cuando la propiedad ya esta animada', () => {
    const source = document();
    const clipA = source.clips[0] as VisualClip;
    clipA.keyframes.rotation = [{ t: 0, value: 0, ease: 'ease-in-out' }];

    const next = writeVisualValue(source, 'a', 'rotation', 2, 45);

    expect((next.clips[0] as VisualClip).keyframes.rotation).toEqual([
      { t: 0, value: 0, ease: 'ease-in-out' },
      { t: 2, value: 45, ease: 'linear' },
    ]);
    expect((next.clips[0] as VisualClip).transform.rotation).toBe(0);
  });

  it('mueve un keyframe a traves de otros y conserva el orden', () => {
    const source = document();
    const clipA = source.clips[0] as VisualClip;
    clipA.keyframes.x = [
      { t: 0, value: 0, ease: 'linear' },
      { t: 1, value: 10, ease: 'linear' },
      { t: 2, value: 20, ease: 'linear' },
    ];

    const next = moveKeyframe(source, 'a', 'x', 1, 3);

    expect((next.clips[0] as VisualClip).keyframes.x.map((keyframe) => keyframe.t)).toEqual([0, 2, 3]);
  });

  it('cambia la curva del keyframe activo sin mutar el documento de origen', () => {
    const source = document();
    const clipA = source.clips[0] as VisualClip;
    clipA.keyframes.x = [{ t: 0, value: 0, ease: 'linear' }];

    const next = setKeyframeEase(source, 'a', 'x', 0, 'hold');

    expect((next.clips[0] as VisualClip).keyframes.x[0].ease).toBe('hold');
    expect((source.clips[0] as VisualClip).keyframes.x[0].ease).toBe('linear');
  });

  it('actualiza cada borde del recorte base y quita la propiedad al borrar su único keyframe', () => {
    const source = document();
    const clipA = source.clips[0] as VisualClip;
    const edges = [
      ['crop_l', 'l'], ['crop_t', 't'], ['crop_r', 'r'], ['crop_b', 'b'],
    ] as const;
    for (const [property, edge] of edges) {
      const next = writeVisualValue(source, 'a', property, 99, 0.25);
      expect((next.clips[0] as VisualClip).transform.crop[edge]).toBe(0.25);
    }

    clipA.keyframes.rotation = [{ t: 0, value: 0, ease: 'linear' }];
    const removed = toggleKeyframe(source, 'a', 'rotation', 0);
    expect((removed.clips[0] as VisualClip).keyframes).toEqual({});
  });

  it('omite la curva si no hay keyframe cercano y conserva la lista si el origen no existe', () => {
    const source = document();
    const clipA = source.clips[0] as VisualClip;
    clipA.keyframes.x = [{ t: 0, value: 0, ease: 'linear' }];
    const ease = setKeyframeEase(source, 'a', 'x', 2, 'hold');
    expect((ease.clips[0] as VisualClip).keyframes.x[0].ease).toBe('linear');
    expect(moveKeyframe(source, 'a', 'x', 10, 3)).toEqual(source);
  });

  it('busca un cuadro libre al mover un keyframe y rechaza transiciones inválidas o duplicadas', () => {
    const source = document();
    const clipA = source.clips[0] as VisualClip;
    clipA.keyframes.x = [0, 1, 2, 4].map((t) => ({ t, value: t, ease: 'linear' as const }));
    const moved = moveKeyframe(source, 'a', 'x', 0, 1);
    expect((moved.clips[0] as VisualClip).keyframes.x.map((frame) => frame.t)).toEqual([1, 31 / 30, 2, 4]);

    expect(addTransitionAtCut(source, 'missing', 4, 'fade', 'x')).toBeNull();
    expect(addTransitionAtCut(source, 'video', 4, 'fade', 'x', 0)).toBeNull();
    const pairAlreadyTransitioned = document();
    pairAlreadyTransitioned.transitions.push({ id: 'existing', track: 'video', a: 'a', b: 'b', type: 'fade', duration: 0.5 });
    expect(addTransitionAtCut(pairAlreadyTransitioned, 'video', 4, 'fade', 'another')).toBeNull();
    const created = addTransitionAtCut(source, 'video', 4, 'fade', 'transition-1', 0.5);
    expect(addTransitionAtCut(created!, 'video', 3.5, 'fade', 'transition-1')).toBeNull();
    expect(addTransitionAtCut(created!, 'video', 3.5, 'fade', 'transition-2')).toBeNull();
    expect(resizeTransition(created!, 'transition-1', Number.NaN)).toBeNull();
  });

  it('agrega una transicion al corte y mueve el segundo clip para crear el solapamiento', () => {
    const source = document();

    const next = addTransitionAtCut(source, 'video', 4, 'fade', 'transition-1', 0.5);

    expect(next?.clips[1].start).toBe(3.5);
    expect(next?.transitions).toEqual([
      { id: 'transition-1', track: 'video', a: 'a', b: 'b', type: 'fade', duration: 0.5 },
    ]);
    expect(source.clips[1].start).toBe(4);
    expect(addTransitionAtCut(source, 'video', 1, 'fade', 'missing')).toBeNull();
  });

  it('cambia la duracion de una transicion y mantiene el solapamiento exacto', () => {
    const source = document();
    const created = addTransitionAtCut(source, 'video', 4, 'fade', 'transition-1', 0.5);
    const next = resizeTransition(created!, 'transition-1', 1);

    expect(next?.transitions[0].duration).toBe(1);
    expect(next?.clips[1].start).toBe(3);
    expect(resizeTransition(source, 'missing', 1)).toBeNull();
  });
});

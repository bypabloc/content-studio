import { cleanup, createEvent, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Timeline } from '@/features/editor/Timeline';
import type { Clip, Doc, VisualClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const queryUrl = vi.hoisted(() => vi.fn(() => '/media/frame'));
vi.mock('@/shared/api/context', () => ({ useApi: () => ({ queryUrl }) }));

afterEach(cleanup);

function clip(id: string, track: string, src: string, start: number, length: number): Clip {
  return { id, track, src, src_in: 0, src_out: length, start, gain_db: 0, fade_in: 0, fade_out: 0 };
}

function document(): Doc {
  return {
    version: 2,
    name: 'demo',
    sample_rate: 48000,
    canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' },
    tracks: [
      { id: 'voice', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80 },
      { id: 'music', kind: 'audio', name: 'Música', volume_db: 0, mute: false, solo: false, locked: false, height: 80 },
    ],
    clips: [clip('voice-clip', 'voice', 'D:/media/voice.wav', 9.9, 2), clip('music-clip', 'music', 'D:/media/music.wav', 0, 2)],
    markers: [{ id: 'marker-1', t: 10, label: 'corte', color: '#f00' }],
    transitions: [],
  };
}

function renderTimeline(magnet = true) {
  const callbacks = {
    onSelectionChange: vi.fn(),
    onPreview: vi.fn(),
    onCommitPreview: vi.fn(),
    onCancelPreview: vi.fn(),
  };
  render(<Timeline doc={document()} selectedIds={[]} playhead={0} zoom={80} magnet={magnet} {...callbacks} />);
  return callbacks;
}

describe('Timeline', () => {
  it('muestra pistas, clips y la regla del proyecto', () => {
    renderTimeline();

    expect(screen.getByRole('group', { name: t('editor.timeline.label') })).toBeTruthy();
    expect(screen.getByText('Voz')).toBeTruthy();
    expect(screen.getByText('Música')).toBeTruthy();
    expect(screen.getByRole('group', { name: t('editor.timeline.ruler') })).toBeTruthy();
    expect(screen.getByRole('button', { name: t('editor.clip.label', { source: 'voice.wav', start: '9.9', end: '11.9' }) })).toBeTruthy();
  });

  it('selecciona clips por el rango arrastrado sobre una pista vacía', () => {
    const callbacks = renderTimeline();
    const lane = screen.getByRole('group', { name: t('editor.timeline.lane', { name: 'Voz' }) });

    fireEvent.pointerDown(lane, { button: 0, clientX: 760, pointerId: 1 });
    fireEvent.pointerMove(lane, { clientX: 960, pointerId: 1 });
    expect(screen.getByRole('img', { name: t('editor.timeline.range') })).toBeTruthy();
    fireEvent.pointerUp(lane, { clientX: 960, pointerId: 1 });

    expect(callbacks.onSelectionChange).toHaveBeenCalledWith(['voice-clip']);
  });

  it('pega el borde izquierdo del clip al marcador al soltarlo a cuatro píxeles', () => {
    const callbacks = renderTimeline();
    const clipButton = screen.getByRole('button', {
      name: t('editor.clip.label', { source: 'voice.wav', start: '9.9', end: '11.9' }),
    });

    fireEvent.pointerDown(clipButton, { button: 0, clientX: 0, pointerId: 1 });
    fireEvent.pointerMove(clipButton, { clientX: 4, pointerId: 1 });
    fireEvent.pointerUp(clipButton, { clientX: 4, pointerId: 1 });

    const preview = callbacks.onPreview.mock.calls.at(-1)?.[0] as Doc;
    expect(preview.clips.find((item) => item.id === 'voice-clip')?.start).toBe(10);
    expect(callbacks.onCommitPreview).toHaveBeenCalledOnce();
  });

  it('mantiene el tiempo exacto con el imán apagado', () => {
    const callbacks = renderTimeline(false);
    const clipButton = screen.getByRole('button', {
      name: t('editor.clip.label', { source: 'voice.wav', start: '9.9', end: '11.9' }),
    });

    fireEvent.pointerDown(clipButton, { button: 0, clientX: 0, pointerId: 1 });
    fireEvent.pointerMove(clipButton, { clientX: 4, pointerId: 1 });
    fireEvent.pointerUp(clipButton, { clientX: 4, pointerId: 1 });

    const preview = callbacks.onPreview.mock.calls.at(-1)?.[0] as Doc;
    expect(preview.clips.find((item) => item.id === 'voice-clip')?.start).toBeCloseTo(9.95);
  });

  it('recibe rutas soltadas en la posición de una pista', () => {
    const onDropFiles = vi.fn();
    render(
      <Timeline
        doc={document()}
        selectedIds={[]}
        playhead={0}
        zoom={80}
        magnet
        onSelectionChange={vi.fn()}
        onPreview={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
        onDropFiles={onDropFiles}
      />,
    );
    const lane = screen.getByRole('group', { name: t('editor.timeline.lane', { name: 'Voz' }) });
    const dataTransfer = { getData: vi.fn(() => JSON.stringify(['D:\\media\\take.wav'])) };

    const drop = createEvent.drop(lane, { dataTransfer });
    Object.defineProperty(drop, 'clientX', { value: 80 });
    fireEvent(lane, drop);

    expect(onDropFiles).toHaveBeenCalledWith(['D:\\media\\take.wav'], 'voice', 1);
  });

  it('recibe transiciones soltadas en una pista o en el fondo', () => {
    const onDropTransition = vi.fn();
    render(
      <Timeline
        doc={document()}
        selectedIds={[]}
        playhead={4}
        zoom={80}
        magnet
        onSelectionChange={vi.fn()}
        onPreview={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
        onDropTransition={onDropTransition}
      />,
    );
    const lane = screen.getByRole('group', { name: t('editor.timeline.lane', { name: 'Voz' }) });
    const timeline = screen.getByRole('group', { name: t('editor.timeline.label') });
    const dataTransfer = { getData: (type: string) => type === 'application/x-editor-transition' ? 'wipeleft' : '' };
    fireEvent.dragOver(lane);
    const laneDrop = createEvent.drop(lane, { dataTransfer });
    const timelineDrop = createEvent.drop(timeline, { dataTransfer });
    Object.defineProperty(laneDrop, 'clientX', { value: 240 });
    Object.defineProperty(timelineDrop, 'clientX', { value: 240 });
    fireEvent(lane, laneDrop);
    fireEvent(timeline, timelineDrop);

    expect(onDropTransition).toHaveBeenNthCalledWith(1, 'wipeleft', 'voice', 3);
    expect(onDropTransition).toHaveBeenNthCalledWith(2, 'wipeleft', undefined, 4);
  });

  it('recibe presets de texto soltados en la pista o en el fondo', () => {
    const onDropText = vi.fn();
    const doc = document();
    doc.tracks.unshift({ id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false });
    render(
      <Timeline
        doc={doc} selectedIds={[]} playhead={4} zoom={80} magnet
        onSelectionChange={vi.fn()} onPreview={vi.fn()} onCommitPreview={vi.fn()} onCancelPreview={vi.fn()}
        onDropText={onDropText}
      />,
    );
    const lane = screen.getByRole('group', { name: t('editor.timeline.lane', { name: 'Video' }) });
    const timeline = screen.getByRole('group', { name: t('editor.timeline.label') });
    const dataTransfer = {
      getData: (type: string) => type === 'application/x-editor-text-preset' ? 'lower-third' : '',
    };
    const laneDrop = createEvent.drop(lane, { dataTransfer });
    const timelineDrop = createEvent.drop(timeline, { dataTransfer });
    Object.defineProperty(laneDrop, 'clientX', { value: 240 });
    fireEvent(lane, laneDrop);
    fireEvent(timeline, timelineDrop);

    expect(onDropText).toHaveBeenNthCalledWith(1, 'lower-third', 'video', 3);
    expect(onDropText).toHaveBeenNthCalledWith(2, 'lower-third', undefined, 4);
  });

  it('muestra keyframes y transiciones y redimensiona solo las transiciones declaradas', () => {
    const base = document();
    const videoTrack = { id: 'video', kind: 'video' as const, name: 'Video', opacity: 1, hidden: false, locked: false };
    const visual = (id: string, start: number): VisualClip => ({
      id, track: 'video', src: `${id}.png`, src_in: 0, src_out: 2, start, fade_in: 0, fade_out: 0, media: 'image',
      transform: { x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
        crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5 },
      keyframes: { x: [{ t: 0, value: 0, ease: 'linear' }, { t: 1, value: 10, ease: 'linear' }] },
    });
    base.tracks.unshift(videoTrack);
    base.clips.push(visual('visual-a', 0), visual('visual-b', 1.5));
    base.transitions = [
      { id: 'missing-target', track: 'video', a: 'visual-a', b: 'missing', type: 'fade', duration: 0.5 },
      { id: 'transition', track: 'video', a: 'visual-a', b: 'visual-b', type: 'fade', duration: 0.5 },
    ];
    const onPreview = vi.fn();
    const onCommitPreview = vi.fn();
    render(
      <Timeline
        doc={base}
        selectedIds={['visual-a']}
        playhead={0}
        zoom={100}
        magnet={false}
        onSelectionChange={vi.fn()}
        onPreview={onPreview}
        onCommitPreview={onCommitPreview}
        onCancelPreview={vi.fn()}
        armedTrackIds={['voice']}
        recordingLevels={{ rms: -18, peak: -6 }}
        onArmedChange={vi.fn()}
      />,
    );

    expect(screen.getByRole('group', { name: t('editor.keyframe.label') })).toBeTruthy();
    const transitionEnd = screen.getByRole('button', { name: t('editor.transition.resize_end') });
    fireEvent.pointerDown(transitionEnd, { pointerId: 30, clientX: 0, button: 0 });
    fireEvent.pointerMove(transitionEnd, { pointerId: 30, clientX: 20 });
    fireEvent.pointerUp(transitionEnd, { pointerId: 30, clientX: 20 });
    expect(onPreview).toHaveBeenCalled();
    expect(onCommitPreview).toHaveBeenCalledOnce();
  });

  it('ignora payloads vacíos o inválidos y admite rutas soltadas en el fondo', () => {
    const onDropFiles = vi.fn();
    render(
      <Timeline
        doc={document()}
        selectedIds={[]}
        playhead={4}
        zoom={80}
        magnet
        onSelectionChange={vi.fn()}
        onPreview={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
        onDropFiles={onDropFiles}
      />,
    );
    const timeline = screen.getByRole('group', { name: t('editor.timeline.label') });
    const lane = screen.getByRole('group', { name: t('editor.timeline.lane', { name: 'Voz' }) });
    for (const payload of ['', '{', '{}']) {
      fireEvent.drop(timeline, { dataTransfer: { getData: () => payload } });
      fireEvent.drop(lane, { dataTransfer: { getData: () => payload } });
    }
    fireEvent.drop(timeline, { dataTransfer: { getData: () => JSON.stringify(['D:/media/fondo.wav']) } });

    expect(onDropFiles).toHaveBeenCalledOnce();
    expect(onDropFiles).toHaveBeenCalledWith(['D:/media/fondo.wav'], undefined, 4);
  });

  it('recorta el borde final al marcador con el imán', () => {
    const base = document();
    base.clips[0] = { ...base.clips[0], start: 0, src_out: 2 };
    base.markers[0] = { ...base.markers[0], t: 2.1 };
    const callbacks = {
      onSelectionChange: vi.fn(), onPreview: vi.fn(), onCommitPreview: vi.fn(), onCancelPreview: vi.fn(),
    };
    render(<Timeline doc={base} selectedIds={[]} playhead={0} zoom={80} magnet {...callbacks} />);
    const end = screen.getByRole('slider', { name: t('editor.clip.trim_end', { source: 'voice.wav' }) });

    fireEvent.pointerDown(end, { button: 0, clientX: 0, pointerId: 1 });
    fireEvent.pointerMove(end, { clientX: 8, pointerId: 1 });
    fireEvent.pointerUp(end, { clientX: 8, pointerId: 1 });

    const preview = callbacks.onPreview.mock.calls.at(-1)?.[0] as Doc;
    expect(preview.clips.find((item) => item.id === 'voice-clip')?.src_out).toBeCloseTo(2.1);
  });

  it('restablece un rango cancelado e ignora el botón secundario', () => {
    const callbacks = renderTimeline();
    const lane = screen.getByRole('group', { name: t('editor.timeline.lane', { name: 'Voz' }) });

    fireEvent.pointerDown(lane, { button: 2, clientX: 100, pointerId: 2 });
    fireEvent.pointerMove(lane, { clientX: 200, pointerId: 2 });
    fireEvent.pointerUp(lane, { clientX: 200, pointerId: 2 });
    fireEvent.pointerDown(lane, { button: 0, clientX: 100, pointerId: 3 });
    fireEvent.pointerCancel(lane, { clientX: 200, pointerId: 3 });
    fireEvent.pointerMove(lane, { clientX: 200, pointerId: 3 });
    fireEvent.pointerUp(lane, { clientX: 200, pointerId: 3 });

    expect(callbacks.onSelectionChange).not.toHaveBeenCalled();
  });

  it('mantiene funcionales los controles de pista con callbacks opcionales', () => {
    render(
      <Timeline
        doc={document()}
        selectedIds={[]}
        playhead={0}
        zoom={80}
        magnet
        onSelectionChange={vi.fn()}
        onPreview={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: t('editor.track.mute', { name: 'Voz' }) }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.track.arm', { name: 'Voz' }) }));
  });
});

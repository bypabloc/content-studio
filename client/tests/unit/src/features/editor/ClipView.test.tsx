import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { ClipView } from '@/features/editor/ClipView';
import type { Clip, Doc } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const queryUrl = vi.hoisted(() => vi.fn((_path: string, query: Record<string, string>) => `/frame?t=${query.t}`));
vi.mock('@/shared/api/context', () => ({ useApi: () => ({ queryUrl }) }));

afterEach(cleanup);

const clip: Clip = {
  id: 'clip-1',
  track: 'voice',
  src: 'D:/media/voice.wav',
  src_in: 0,
  src_out: 2,
  start: 1,
  gain_db: 0,
  fade_in: 0,
  fade_out: 0,
};

const doc: Doc = {
  version: 2,
  name: 'demo',
  sample_rate: 48000,
  canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' },
  tracks: [{ id: 'voice', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80 }],
  clips: [clip],
  markers: [],
  transitions: [],
};

describe('ClipView', () => {
  it('expone el clip y sus controles accesibles para recortar los dos bordes', () => {
    render(
      <ClipView
        clip={clip}
        doc={doc}
        selected
        selectedIds={['clip-1']}
        zoom={80}
        magnet
        playhead={0}
        locked={false}
        onSelect={vi.fn()}
        onPreview={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
      />,
    );

    expect(
      screen.getByRole('button', { name: t('editor.clip.label', { source: 'voice.wav', start: '1.0', end: '3.0' }) }),
    ).toBeTruthy();
    expect(screen.getByRole('slider', { name: t('editor.clip.trim_start', { source: 'voice.wav' }) })).toBeTruthy();
    expect(screen.getByRole('slider', { name: t('editor.clip.trim_end', { source: 'voice.wav' }) })).toBeTruthy();
  });

  it('selecciona un clip al hacer clic y no guarda un arrastre sin movimiento', () => {
    const onSelect = vi.fn();
    const onPreview = vi.fn();
    const onCommitPreview = vi.fn();
    render(
      <ClipView
        clip={clip}
        doc={doc}
        selected={false}
        selectedIds={[]}
        zoom={80}
        magnet
        playhead={0}
        locked={false}
        onSelect={onSelect}
        onPreview={onPreview}
        onCommitPreview={onCommitPreview}
        onCancelPreview={vi.fn()}
      />,
    );
    const button = screen.getByRole('button', {
      name: t('editor.clip.label', { source: 'voice.wav', start: '1.0', end: '3.0' }),
    });

    fireEvent.click(button);
    fireEvent.pointerDown(button, { button: 0, clientX: 0, pointerId: 4 });
    fireEvent.pointerUp(button, { clientX: 0, pointerId: 4 });

    expect(onSelect).toHaveBeenCalledWith(['clip-1']);
    expect(onPreview).not.toHaveBeenCalled();
    expect(onCommitPreview).not.toHaveBeenCalled();
  });

  it('no mueve una pista bloqueada y cancela un arrastre interrumpido', () => {
    const onPreview = vi.fn();
    const onCancelPreview = vi.fn();
    const onCommitPreview = vi.fn();
    const props = {
      clip,
      doc,
      selected: true,
      selectedIds: ['clip-1'],
      zoom: 80,
      magnet: false,
      playhead: 0,
      onSelect: vi.fn(),
      onPreview,
      onCommitPreview,
      onCancelPreview,
    };
    const { rerender } = render(<ClipView {...props} locked />);
    const label = t('editor.clip.label', { source: 'voice.wav', start: '1.0', end: '3.0' });
    const lockedButton = screen.getByRole('button', { name: label });
    fireEvent.pointerDown(lockedButton, { button: 0, clientX: 0, pointerId: 5 });
    fireEvent.pointerMove(lockedButton, { clientX: 10, pointerId: 5 });
    fireEvent.pointerUp(lockedButton, { clientX: 10, pointerId: 5 });
    expect(onPreview).not.toHaveBeenCalled();

    rerender(<ClipView {...props} locked={false} />);
    const button = screen.getByRole('button', { name: label });
    fireEvent.pointerDown(button, { button: 0, clientX: 0, pointerId: 6 });
    fireEvent.pointerMove(button, { clientX: 20, pointerId: 6 });
    fireEvent.pointerCancel(button, { clientX: 20, pointerId: 6 });

    expect(onPreview).toHaveBeenCalled();
    expect(onCancelPreview).toHaveBeenCalledOnce();
    expect(onCommitPreview).not.toHaveBeenCalled();
  });

  it('mueve en bloque los clips seleccionados', () => {
    const group: Doc = { ...doc, clips: [clip, { ...clip, id: 'clip-2', start: 4 }] };
    const onPreview = vi.fn();
    render(
      <ClipView
        clip={clip}
        doc={group}
        selected
        selectedIds={['clip-1', 'clip-2']}
        zoom={80}
        magnet={false}
        playhead={0}
        locked={false}
        onSelect={vi.fn()}
        onPreview={onPreview}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
      />,
    );
    const button = screen.getByRole('button', {
      name: t('editor.clip.label', { source: 'voice.wav', start: '1.0', end: '3.0' }),
    });

    fireEvent.pointerDown(button, { button: 0, clientX: 0, pointerId: 7 });
    fireEvent.pointerMove(button, { clientX: 80, pointerId: 7 });

    const preview = onPreview.mock.calls.at(-1)?.[0] as Doc;
    expect(preview.clips.map(({ start }) => start)).toEqual([2, 5]);
  });

  it('recorta con las flechas y descarta un borde inválido', () => {
    const onPreview = vi.fn();
    const onCommitPreview = vi.fn();
    const props = {
      clip,
      doc,
      selected: true,
      selectedIds: ['clip-1'],
      zoom: 80,
      magnet: false,
      playhead: 0,
      locked: false,
      onSelect: vi.fn(),
      onPreview,
      onCommitPreview,
      onCancelPreview: vi.fn(),
    };
    const { rerender } = render(<ClipView {...props} />);
    let start = screen.getByRole('slider', { name: t('editor.clip.trim_start', { source: 'voice.wav' }) });
    fireEvent.keyDown(start, { key: 'ArrowRight' });
    fireEvent.keyDown(start, { key: 'x' });
    expect(onPreview.mock.calls[0][0].clips[0].start).toBeCloseTo(1.1);
    expect(onCommitPreview).toHaveBeenCalledOnce();

    const shortClip = { ...clip, start: 0 };
    rerender(<ClipView {...props} clip={shortClip} doc={{ ...doc, clips: [shortClip] }} />);
    start = screen.getByRole('slider', { name: t('editor.clip.trim_start', { source: 'voice.wav' }) });
    onPreview.mockClear();
    onCommitPreview.mockClear();
    fireEvent.keyDown(start, { key: 'ArrowLeft' });
    expect(onPreview).not.toHaveBeenCalled();
    expect(onCommitPreview).not.toHaveBeenCalled();
  });

  it('genera miniaturas de video según el zoom de la línea de tiempo', () => {
    const video: Clip = {
      id: 'video-1', track: 'video', src: 'D:/media/video.mp4', src_in: 2, src_out: 4, start: 1,
      fade_in: 0, fade_out: 0, media: 'video',
      transform: {
        x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
        crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
      },
      keyframes: {},
    };
    const { container } = render(
      <ClipView
        clip={video}
        doc={doc}
        selected={false}
        selectedIds={[]}
        zoom={80}
        magnet
        playhead={0}
        locked={false}
        onSelect={vi.fn()}
        onPreview={vi.fn()}
        onCommitPreview={vi.fn()}
        onCancelPreview={vi.fn()}
      />,
    );

    expect(container.querySelectorAll('img')).toHaveLength(2);
    expect(queryUrl).toHaveBeenCalledWith('/media/frame', { path: 'D:/media/video.mp4', t: '2' });
  });
});

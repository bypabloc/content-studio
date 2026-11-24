import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Inspector } from '@/features/editor/Inspector';
import type { Doc, VideoClip, VisualClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

const clip: VisualClip = {
  id: 'logo', track: 'video', src: 'logo.png', src_in: 0, src_out: 4, start: 2, fade_in: 0, fade_out: 0, media: 'image',
  transform: {
    x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
    crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
  },
  keyframes: {
    x: [
      { t: 0, value: 0, ease: 'linear' },
      { t: 2, value: 40, ease: 'linear' },
      { t: 4, value: 80, ease: 'ease-in-out' },
    ],
  },
};

const doc: Doc = {
  version: 2, name: 'demo', sample_rate: 48000,
  canvas: { width: 1920, height: 1080, fps: 30, background: '#000000' },
  tracks: [{ id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false }],
  clips: [clip], markers: [], transitions: [],
};

describe('Inspector', () => {
  it('edita una propiedad, expone el estado del keyframe y navega entre keyframes', () => {
    const onChange = vi.fn();
    const onToggleKeyframe = vi.fn();
    const onSeek = vi.fn();
    render(
      <Inspector
        doc={doc}
        clipId="logo"
        time={4}
        onChange={onChange}
        onSpeedChange={vi.fn()}
        onToggleKeyframe={onToggleKeyframe}
        onEaseChange={vi.fn()}
        onSeek={onSeek}
        onCanvasChange={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(t('editor.inspector.property_x')), { target: { value: '120' } });
    expect(onChange).toHaveBeenCalledWith('x', 120);
    const keyframe = screen.getByRole('button', {
      name: t('editor.inspector.keyframe', { property: t('editor.inspector.property_x') }),
    });
    expect(keyframe.getAttribute('aria-pressed')).toBe('true');
    fireEvent.click(keyframe);
    expect(onToggleKeyframe).toHaveBeenCalledWith('x');

    fireEvent.click(screen.getByRole('button', { name: t('editor.inspector.previous') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.inspector.next') }));
    expect(onSeek).toHaveBeenNthCalledWith(1, 2);
    expect(onSeek).toHaveBeenNthCalledWith(2, 6);
  });

  it('muestra y actualiza los ajustes del lienzo sin clips seleccionados', () => {
    const onCanvasChange = vi.fn();
    render(
      <Inspector
        doc={doc}
        clipId={null}
        time={0}
        onChange={vi.fn()}
        onSpeedChange={vi.fn()}
        onToggleKeyframe={vi.fn()}
        onEaseChange={vi.fn()}
        onSeek={vi.fn()}
        onCanvasChange={onCanvasChange}
      />,
    );

    expect(screen.getByText(t('editor.inspector.no_selection'))).toBeTruthy();
    fireEvent.change(screen.getByLabelText(t('editor.inspector.canvas_width')), { target: { value: '2048' } });
    expect(onCanvasChange).toHaveBeenCalledWith({ width: 2048 });
  });

  it('permite cambiar la velocidad de un clip de video entre 0.25× y 4×', () => {
    const onSpeedChange = vi.fn();
    const video: VideoClip = { ...clip, media: 'video', speed: 1 };
    render(
      <Inspector
        doc={{ ...doc, version: 3, clips: [video] }}
        clipId="logo"
        time={0}
        onChange={vi.fn()}
        onSpeedChange={onSpeedChange}
        onToggleKeyframe={vi.fn()}
        onEaseChange={vi.fn()}
        onSeek={vi.fn()}
        onCanvasChange={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(t('editor.inspector.speed')), { target: { value: '2' } });
    expect(onSpeedChange).toHaveBeenCalledWith('logo', 2);
  });
});

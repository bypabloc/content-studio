import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { KeyframeLane } from '@/features/editor/KeyframeLane';
import type { Doc, VisualClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

const clip: VisualClip = {
  id: 'logo', track: 'video', src: 'logo.png', src_in: 0, src_out: 4, start: 0, fade_in: 0, fade_out: 0, media: 'image',
  transform: {
    x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
    crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
  },
  keyframes: { x: [{ t: 0, value: 0, ease: 'linear' }, { t: 2, value: 100, ease: 'linear' }] },
};
const doc: Doc = {
  version: 2, name: 'demo', sample_rate: 48000,
  canvas: { width: 1280, height: 720, fps: 30, background: '#000000' },
  tracks: [{ id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false }],
  clips: [clip], markers: [{ id: 'marker', t: 3, label: 'Corte', color: '#ef4444' }], transitions: [],
};

describe('KeyframeLane', () => {
  it('muestra rombos y pega el arrastre al marcador más cercano', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    render(<KeyframeLane doc={doc} clipId="logo" zoom={100} magnet playhead={0} onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} />);
    const row = screen.getByRole('group', { name: t('editor.keyframe.lane', { property: t('editor.inspector.property_x') }) });
    vi.spyOn(row, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 0, left: 0, top: 0, right: 400, bottom: 32, width: 400, height: 32,
      toJSON: () => ({}),
    });
    const point = screen.getByRole('button', {
      name: t('editor.keyframe.point', { property: t('editor.inspector.property_x'), time: '2' }),
    });
    fireEvent.pointerDown(point, { pointerId: 8, clientX: 200, button: 0 });
    fireEvent.pointerMove(point, { pointerId: 8, clientX: 295 });
    fireEvent.pointerUp(point, { pointerId: 8, clientX: 295 });

    const edited = onPreviewDoc.mock.calls.at(-1)?.[0] as Doc;
    expect((edited.clips[0] as VisualClip).keyframes.x.map((frame) => frame.t)).toEqual([0, 3]);
    expect(onCommitPreview).toHaveBeenCalledOnce();
  });

  it('permite mover sin imán y cancela una edición que no se confirma', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    const onCancelPreview = vi.fn();
    render(
      <KeyframeLane
        doc={doc}
        clipId="logo"
        zoom={100}
        magnet={false}
        playhead={0}
        onPreviewDoc={onPreviewDoc}
        onCommitPreview={onCommitPreview}
        onCancelPreview={onCancelPreview}
      />,
    );
    const row = screen.getByRole('group', { name: t('editor.keyframe.lane', { property: t('editor.inspector.property_x') }) });
    vi.spyOn(row, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 0, left: 0, top: 0, right: 400, bottom: 32, width: 400, height: 32,
      toJSON: () => ({}),
    });
    const point = screen.getByRole('button', {
      name: t('editor.keyframe.point', { property: t('editor.inspector.property_x'), time: '2' }),
    });
    fireEvent.pointerDown(point, { pointerId: 14, clientX: 200, button: 0 });
    fireEvent.pointerMove(point, { pointerId: 14, clientX: 235 });
    const edited = onPreviewDoc.mock.calls.at(-1)?.[0] as Doc;
    expect((edited.clips[0] as VisualClip).keyframes.x[1].t).toBeCloseTo(71 / 30);
    fireEvent.pointerCancel(point, { pointerId: 14 });
    expect(onCancelPreview).toHaveBeenCalledOnce();
    expect(onCommitPreview).not.toHaveBeenCalled();
  });

  it('no dibuja carriles sin selección visual ni keyframes', () => {
    const empty = structuredClone(doc);
    (empty.clips[0] as VisualClip).keyframes = {};
    const props = {
      doc: empty,
      zoom: 100,
      magnet: true,
      playhead: 0,
      onPreviewDoc: vi.fn(),
      onCommitPreview: vi.fn(),
    };

    const { rerender, container } = render(<KeyframeLane {...props} clipId={null} />);
    expect(container.firstChild).toBeNull();
    rerender(<KeyframeLane {...props} clipId="logo" />);
    expect(container.firstChild).toBeNull();
  });

  it('ignora movimientos bloqueados y gestos que se cancelan antes de cambiar', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    const { rerender } = render(
      <KeyframeLane doc={doc} clipId="logo" zoom={100} magnet playhead={0} locked onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} />,
    );
    const point = screen.getByRole('button', {
      name: t('editor.keyframe.point', { property: t('editor.inspector.property_x'), time: '2' }),
    });
    point.removeAttribute('disabled');
    fireEvent.pointerDown(point, { pointerId: 15, clientX: 200, button: 0 });
    fireEvent.pointerMove(point, { pointerId: 15, clientX: 250 });
    fireEvent.pointerUp(point, { pointerId: 15, clientX: 250 });
    expect(onPreviewDoc).not.toHaveBeenCalled();

    rerender(<KeyframeLane doc={doc} clipId="logo" zoom={100} magnet playhead={0} onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} />);
    const unlockedPoint = screen.getByRole('button', {
      name: t('editor.keyframe.point', { property: t('editor.inspector.property_x'), time: '2' }),
    });
    fireEvent.pointerMove(unlockedPoint, { pointerId: 16, clientX: 250 });
    fireEvent.pointerUp(unlockedPoint, { pointerId: 16, clientX: 250 });
    fireEvent.pointerDown(unlockedPoint, { pointerId: 17, clientX: 200, button: 0 });
    fireEvent.pointerCancel(unlockedPoint, { pointerId: 17 });
    expect(onPreviewDoc).not.toHaveBeenCalled();
    expect(onCommitPreview).not.toHaveBeenCalled();
  });

  it('acepta cancelar un movimiento posterior sin callback opcional', () => {
    render(<KeyframeLane doc={doc} clipId="logo" zoom={100} magnet={false} playhead={0} onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);
    const row = screen.getByRole('group', { name: t('editor.keyframe.lane', { property: t('editor.inspector.property_x') }) });
    vi.spyOn(row, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 0, left: 0, top: 0, right: 400, bottom: 32, width: 400, height: 32,
      toJSON: () => ({}),
    });
    const point = screen.getByRole('button', {
      name: t('editor.keyframe.point', { property: t('editor.inspector.property_x'), time: '2' }),
    });
    fireEvent.pointerDown(point, { pointerId: 18, clientX: 200, button: 0 });
    fireEvent.pointerMove(point, { pointerId: 18, clientX: 210 });
    fireEvent.pointerCancel(point, { pointerId: 18 });
  });
});

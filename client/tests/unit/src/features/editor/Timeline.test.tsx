import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Timeline } from '@/features/editor/Timeline';
import type { Clip, Doc } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

function clip(id: string, track: string, src: string, start: number, length: number): Clip {
  return { id, track, src, src_in: 0, src_out: length, start, gain_db: 0, fade_in: 0, fade_out: 0 };
}

function document(): Doc {
  return {
    version: 1,
    name: 'demo',
    sample_rate: 48000,
    tracks: [
      { id: 'voice', kind: 'audio', name: 'Voz', volume_db: 0, mute: false, solo: false, locked: false, height: 80 },
      { id: 'music', kind: 'audio', name: 'Música', volume_db: 0, mute: false, solo: false, locked: false, height: 80 },
    ],
    clips: [clip('voice-clip', 'voice', 'D:/media/voice.wav', 9.9, 2), clip('music-clip', 'music', 'D:/media/music.wav', 0, 2)],
    markers: [{ id: 'marker-1', t: 10, label: 'corte', color: '#f00' }],
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

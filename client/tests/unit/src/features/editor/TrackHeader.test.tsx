import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { TrackHeader } from '@/features/editor/TrackHeader';
import type { Track } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const track: Track = {
  id: 'voice',
  kind: 'audio',
  name: 'Voz',
  volume_db: 0,
  mute: false,
  solo: false,
  locked: false,
  height: 80,
};

afterEach(cleanup);

describe('TrackHeader', () => {
  it('muestra el nombre y el volumen accesible de la pista', () => {
    render(<TrackHeader track={track} armed={false} onChange={vi.fn()} onArmedChange={vi.fn()} />);

    expect(screen.getByText('Voz')).toBeTruthy();
    expect(screen.getByRole('slider', { name: t('editor.track.volume', { name: 'Voz' }) })).toBeTruthy();
  });

  it('cambia el volumen con la operación setTrack', () => {
    const onChange = vi.fn();
    render(<TrackHeader track={track} armed={false} onChange={onChange} onArmedChange={vi.fn()} />);

    fireEvent.change(screen.getByRole('slider', { name: t('editor.track.volume', { name: 'Voz' }) }), {
      target: { value: '-6' },
    });

    expect(onChange).toHaveBeenCalledWith({ type: 'setTrack', id: 'voice', changes: { volume_db: -6 } });
  });

  it('alterna mute con M y anuncia el atajo', () => {
    const onChange = vi.fn();
    render(<TrackHeader track={track} armed={false} onChange={onChange} onArmedChange={vi.fn()} />);

    const mute = screen.getByRole('button', { name: t('editor.track.mute', { name: 'Voz' }) });
    expect(mute.getAttribute('aria-keyshortcuts')).toBe('M');
    fireEvent.keyDown(mute, { key: 'm' });

    expect(onChange).toHaveBeenCalledWith({ type: 'setTrack', id: 'voice', changes: { mute: true } });
  });

  it('alterna solo, bloqueo y armado con sus controles', () => {
    const onChange = vi.fn();
    const onArmedChange = vi.fn();
    render(<TrackHeader track={track} armed={false} onChange={onChange} onArmedChange={onArmedChange} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.track.solo', { name: 'Voz' }) }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.track.lock', { name: 'Voz' }) }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.track.arm', { name: 'Voz' }) }));

    expect(onChange).toHaveBeenNthCalledWith(1, { type: 'setTrack', id: 'voice', changes: { solo: true } });
    expect(onChange).toHaveBeenNthCalledWith(2, { type: 'setTrack', id: 'voice', changes: { locked: true } });
    expect(onArmedChange).toHaveBeenCalledWith(true);
  });

  it('ignora otras teclas para el atajo de mute', () => {
    const onChange = vi.fn();
    render(<TrackHeader track={track} armed={false} onChange={onChange} onArmedChange={vi.fn()} />);

    fireEvent.keyDown(screen.getByRole('button', { name: t('editor.track.mute', { name: 'Voz' }) }), { key: 'x' });

    expect(onChange).not.toHaveBeenCalled();
  });
});

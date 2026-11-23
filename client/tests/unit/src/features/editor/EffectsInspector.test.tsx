import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { EffectsInspector } from '@/features/editor/EffectsInspector';
import type { ImageClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

afterEach(() => {
  cleanup();
  Reflect.deleteProperty(window, 'EyeDropper');
});

const clip: ImageClip = {
  id: 'image-1', track: 'video', src: 'media/image.png', media: 'image', src_in: 0, src_out: 1, start: 0,
  fade_in: 0, fade_out: 0, blend_mode: 'normal', transform: {
    x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
    crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
  }, keyframes: {},
};

describe('EffectsInspector', () => {
  it('cambia el modo de fusión y ajusta los controles de chroma', async () => {
    const onChange = vi.fn();
    const selected = { ...clip, chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1 } };
    const user = userEvent.setup();
    render(<EffectsInspector clip={selected} onChange={onChange} />);

    await user.click(await screen.findByRole('combobox', { name: t('editor.effects.mode') }));
    await user.click(await screen.findByRole('option', { name: t('editor.effects.blend.multiply') }));
    fireEvent.change(screen.getByLabelText(t('editor.effects.chroma.color')), { target: { value: '#ff0000' } });
    fireEvent.change(screen.getByLabelText(t('editor.effects.chroma.similarity')), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText(t('editor.effects.chroma.blend')), { target: { value: '-1' } });
    fireEvent.click(screen.getByLabelText(t('editor.effects.chroma.despill')));

    expect(onChange).toHaveBeenCalledWith(clip.id, { blend_mode: 'multiply' });
    expect(onChange).toHaveBeenCalledWith(clip.id, {
      chroma: { color: '#ff0000', similarity: 0.2, blend: 0.1 },
    });
    expect(onChange).toHaveBeenCalledWith(clip.id, {
      chroma: { color: '#00ff00', similarity: 1, blend: 0.1 },
    });
    expect(onChange).toHaveBeenCalledWith(clip.id, {
      chroma: { color: '#00ff00', similarity: 0.2, blend: 0 },
    });
    expect(onChange).toHaveBeenCalledWith(clip.id, {
      chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1, despill: true },
    });

    fireEvent.click(screen.getByRole('button', { name: t('editor.effects.chroma.remove') }));
    expect(onChange).toHaveBeenLastCalledWith(clip.id, { chroma: null });
  });

  it('informa si el cuentagotas del navegador no está disponible', () => {
    const onChange = vi.fn();
    const selected = { ...clip, chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1 } };
    render(<EffectsInspector clip={selected} onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.effects.chroma.pick') }));

    expect(screen.getByRole('alert').textContent).toBe(t('editor.effects.chroma.error'));
    expect(onChange).not.toHaveBeenCalled();
  });

  it('ignora la cancelación del cuentagotas', async () => {
    const onChange = vi.fn();
    const selected = { ...clip, chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1 } };
    const open = vi.fn().mockRejectedValue(new Error('cancelled'));
    Object.defineProperty(window, 'EyeDropper', { configurable: true, value: class { open = open; } });
    render(<EffectsInspector clip={selected} onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.effects.chroma.pick') }));
    await waitFor(() => expect(open).toHaveBeenCalledOnce());

    expect(onChange).not.toHaveBeenCalled();
  });

  it('no renderiza controles sin un clip visual', () => {
    const { container } = render(<EffectsInspector clip={null} onChange={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('enables chroma key with the documented defaults', () => {
    const onChange = vi.fn();
    render(<EffectsInspector clip={clip} onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.effects.chroma.enable') }));

    expect(onChange).toHaveBeenCalledWith(clip.id, {
      chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1 },
    });
  });

  it('uses the screen color picker to set the chroma key', async () => {
    const onChange = vi.fn();
    const selected = { ...clip, chroma: { color: '#00ff00', similarity: 0.2, blend: 0.1 } };
    const open = vi.fn().mockResolvedValue({ sRGBHex: '#ff0000' });
    Object.defineProperty(window, 'EyeDropper', { configurable: true, value: class { open = open; } });
    render(<EffectsInspector clip={selected} onChange={onChange} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.effects.chroma.pick') }));

    await waitFor(() => expect(onChange).toHaveBeenCalledWith(clip.id, {
      chroma: { color: '#ff0000', similarity: 0.2, blend: 0.1 },
    }));
    expect(open).toHaveBeenCalledOnce();
  });
});

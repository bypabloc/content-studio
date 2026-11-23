import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { TransitionZone } from '@/features/editor/TransitionZone';
import type { Transition } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

const transition: Transition = {
  id: 'transition-1', track: 'video', a: 'clip-a', b: 'clip-b', type: 'fade', duration: 0.5,
};

describe('TransitionZone', () => {
  it('expone ambos bordes, localiza la transición y cambia la duración al arrastrarlos', () => {
    const onResize = vi.fn();
    const onCommitResize = vi.fn();
    render(<TransitionZone transition={transition} left={350} zoom={100} locked={false} onResize={onResize} onCommitResize={onCommitResize} />);

    const start = screen.getByRole('button', { name: t('editor.transition.resize_start') });
    fireEvent.pointerDown(start, { pointerId: 10, clientX: 350, button: 0 });
    fireEvent.pointerMove(start, { pointerId: 10, clientX: 330 });
    fireEvent.pointerUp(start, { pointerId: 10, clientX: 330 });

    expect(screen.getByRole('group', { name: t('editor.transition.zone', { type: t('editor.transitions.fade') }) })).toBeTruthy();
    expect(onResize).toHaveBeenCalledWith('transition-1', 0.7);
    expect(onCommitResize).toHaveBeenCalledOnce();
  });

  it('redimensiona desde el final, limita una transición positiva y cancela el ajuste', () => {
    const onResize = vi.fn();
    const onCommitResize = vi.fn();
    const onCancelResize = vi.fn();
    render(
      <TransitionZone
        transition={transition}
        left={350}
        zoom={100}
        locked={false}
        onResize={onResize}
        onCommitResize={onCommitResize}
        onCancelResize={onCancelResize}
      />,
    );

    const end = screen.getByRole('button', { name: t('editor.transition.resize_end') });
    fireEvent.pointerDown(end, { pointerId: 11, clientX: 100, button: 0 });
    fireEvent.pointerMove(end, { pointerId: 11, clientX: 0 });
    fireEvent.pointerCancel(end, { pointerId: 11 });

    expect(onResize).toHaveBeenCalledWith('transition-1', 1 / 120);
    expect(onCancelResize).toHaveBeenCalledOnce();
    expect(onCommitResize).not.toHaveBeenCalled();
  });

  it('no inicia el arrastre si la pista está bloqueada ni confirma un gesto cancelado sin movimiento', () => {
    const onResize = vi.fn();
    const onCommitResize = vi.fn();
    const { rerender } = render(
      <TransitionZone transition={transition} left={0} zoom={100} locked onResize={onResize} onCommitResize={onCommitResize} />,
    );

    const start = screen.getByRole('button', { name: t('editor.transition.resize_start') });
    fireEvent.pointerDown(start, { pointerId: 12, clientX: 0, button: 0 });
    fireEvent.pointerMove(start, { pointerId: 12, clientX: 100 });
    fireEvent.pointerUp(start, { pointerId: 12, clientX: 100 });
    expect(start.hasAttribute('disabled')).toBe(true);
    expect(onResize).not.toHaveBeenCalled();
    expect(onCommitResize).not.toHaveBeenCalled();
    start.removeAttribute('disabled');
    fireEvent.pointerDown(start, { pointerId: 19, clientX: 0, button: 0 });
    fireEvent.pointerMove(start, { pointerId: 19, clientX: 10 });
    fireEvent.pointerUp(start, { pointerId: 19, clientX: 10 });
    expect(onResize).not.toHaveBeenCalled();

    rerender(
      <TransitionZone transition={transition} left={0} zoom={100} locked={false} onResize={onResize} onCommitResize={onCommitResize} />,
    );
    fireEvent.pointerDown(start, { pointerId: 13, clientX: 0, button: 0 });
    fireEvent.pointerCancel(start, { pointerId: 13 });
    expect(onCommitResize).not.toHaveBeenCalled();
  });

  it('acepta cancelar un ajuste movido sin callback opcional', () => {
    render(<TransitionZone transition={transition} left={0} zoom={100} locked={false} onResize={vi.fn()} onCommitResize={vi.fn()} />);
    const start = screen.getByRole('button', { name: t('editor.transition.resize_start') });
    fireEvent.pointerDown(start, { pointerId: 14, clientX: 0, button: 0 });
    fireEvent.pointerMove(start, { pointerId: 14, clientX: 5 });
    fireEvent.pointerCancel(start, { pointerId: 14 });
  });
});

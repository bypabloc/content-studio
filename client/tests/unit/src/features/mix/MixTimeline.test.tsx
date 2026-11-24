import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { MixTimeline } from '@/features/mix/MixTimeline';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

describe('MixTimeline', () => {
  it('mueve una región con las flechas en pasos de 0,1 s (AC-6)', () => {
    const onChange = vi.fn();
    render(<MixTimeline regions={[[1, 2]]} duration={6} onChange={onChange} />);

    fireEvent.keyDown(screen.getByRole('button', { name: t('mix.region.label', { n: 1 }) }), { key: 'ArrowRight' });

    expect(onChange).toHaveBeenCalledWith([[1.1, 2.1]]);
  });

  it('no mueve una región más allá del final de la mezcla', () => {
    const onChange = vi.fn();
    render(<MixTimeline regions={[[5, 6]]} duration={6} onChange={onChange} />);

    fireEvent.keyDown(screen.getByRole('button', { name: t('mix.region.label', { n: 1 }) }), { key: 'ArrowRight' });

    expect(onChange).toHaveBeenCalledWith([[5, 6]]);
  });

  it('borra la región seleccionada con Supr', () => {
    const onChange = vi.fn();
    render(<MixTimeline regions={[[1, 2], [3, 4]]} duration={6} onChange={onChange} />);

    fireEvent.keyDown(screen.getByRole('button', { name: t('mix.region.label', { n: 1 }) }), { key: 'Delete' });

    expect(onChange).toHaveBeenCalledWith([[3, 4]]);
  });

  it('no baja de cero al mover hacia atrás', () => {
    const onChange = vi.fn();
    render(<MixTimeline regions={[[0.05, 1]]} duration={6} onChange={onChange} />);

    fireEvent.keyDown(screen.getByRole('button', { name: t('mix.region.label', { n: 1 }) }), { key: 'ArrowLeft' });

    expect(onChange).toHaveBeenCalledWith([[0, 1]]);
  });

  it('Retroceso también borra la región', () => {
    const onChange = vi.fn();
    render(<MixTimeline regions={[[1, 2]]} duration={6} onChange={onChange} />);

    fireEvent.keyDown(screen.getByRole('button', { name: t('mix.region.label', { n: 1 }) }), { key: 'Backspace' });

    expect(onChange).toHaveBeenCalledWith([]);
  });

  it('otras teclas no cambian nada', () => {
    const onChange = vi.fn();
    render(<MixTimeline regions={[[1, 2]]} duration={6} onChange={onChange} />);

    fireEvent.keyDown(screen.getByRole('button', { name: t('mix.region.label', { n: 1 }) }), { key: 'a' });

    expect(onChange).not.toHaveBeenCalled();
  });
});

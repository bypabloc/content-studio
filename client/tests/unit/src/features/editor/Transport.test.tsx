import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Transport } from '@/features/editor/Transport';
import { t } from '@/shared/i18n/t';

afterEach(cleanup);

function renderTransport(overrides: Partial<React.ComponentProps<typeof Transport>> = {}) {
  const props = {
    playing: true,
    recording: false,
    magnet: false,
    zoom: 80,
    onStart: vi.fn(),
    onPlayingChange: vi.fn(),
    onStop: vi.fn(),
    onRecordingChange: vi.fn(),
    onMagnetChange: vi.fn(),
    onZoomChange: vi.fn(),
    ...overrides,
  };
  render(<Transport {...props} />);
  return props;
}

describe('Transport', () => {
  it('muestra controles etiquetados y va al inicio con Home', () => {
    const props = renderTransport();
    const toolbar = screen.getByRole('toolbar', { name: t('editor.transport.label') });

    expect(screen.getByRole('button', { name: t('editor.transport.start') })).toBeTruthy();
    fireEvent.keyDown(toolbar, { key: 'Home' });

    expect(props.onStart).toHaveBeenCalledOnce();
  });

  it('reproduce o pausa con Space y con el control', () => {
    const props = renderTransport({ playing: true });
    const toolbar = screen.getByRole('toolbar', { name: t('editor.transport.label') });

    fireEvent.keyDown(toolbar, { key: ' ' });
    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.pause') }));

    expect(props.onPlayingChange).toHaveBeenNthCalledWith(1, false);
    expect(props.onPlayingChange).toHaveBeenNthCalledWith(2, false);
  });

  it('inicia la grabación con R y alterna el imán con N', () => {
    const props = renderTransport();
    const toolbar = screen.getByRole('toolbar', { name: t('editor.transport.label') });

    fireEvent.keyDown(toolbar, { key: 'r' });
    fireEvent.keyDown(toolbar, { key: 'n' });

    expect(props.onRecordingChange).toHaveBeenCalledWith(true);
    expect(props.onMagnetChange).toHaveBeenCalledWith(true);
  });

  it('detiene y cambia el zoom con los botones más y menos', () => {
    const props = renderTransport();

    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.stop') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.zoom_in') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.zoom_out') }));

    expect(props.onStop).toHaveBeenCalledOnce();
    expect(props.onPlayingChange).toHaveBeenCalledWith(false);
    expect(props.onZoomChange).toHaveBeenNthCalledWith(1, 160);
    expect(props.onZoomChange).toHaveBeenNthCalledWith(2, 40);
  });

  it('aplica los atajos de zoom y omite teclas repetidas o desconocidas', () => {
    const props = renderTransport({ playing: false });
    const toolbar = screen.getByRole('toolbar', { name: t('editor.transport.label') });

    fireEvent.keyDown(toolbar, { key: '=' });
    fireEvent.keyDown(toolbar, { key: '_' });
    fireEvent.keyDown(toolbar, { key: 'r', repeat: true });
    fireEvent.keyDown(toolbar, { key: 'x' });

    expect(props.onZoomChange).toHaveBeenNthCalledWith(1, 160);
    expect(props.onZoomChange).toHaveBeenNthCalledWith(2, 40);
    expect(props.onRecordingChange).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.play') }));
    expect(props.onPlayingChange).toHaveBeenCalledWith(true);
  });

  it('detener también apaga una grabación activa', () => {
    const props = renderTransport({ recording: true });

    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.stop') }));

    expect(props.onRecordingChange).toHaveBeenCalledWith(false);
  });

  it('alterna grabación e imán desde sus botones', () => {
    const props = renderTransport();

    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.record') }));
    fireEvent.click(screen.getByRole('button', { name: t('editor.transport.magnet') }));

    expect(props.onRecordingChange).toHaveBeenCalledWith(true);
    expect(props.onMagnetChange).toHaveBeenCalledWith(true);
  });

  it('no permite hacer zoom fuera del rango', () => {
    renderTransport({ zoom: 320 });
    expect((screen.getByRole('button', { name: t('editor.transport.zoom_in') }) as HTMLButtonElement).disabled).toBe(
      true,
    );

    cleanup();
    renderTransport({ zoom: 5 });
    expect((screen.getByRole('button', { name: t('editor.transport.zoom_out') }) as HTMLButtonElement).disabled).toBe(
      true,
    );
  });
});

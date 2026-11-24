import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { TextInspector } from '@/features/editor/TextInspector';
import type { TextClip } from '@/features/editor/model/types';
import type { EditorFont } from '@/features/editor/text/fonts';
import { t } from '@/shared/i18n/t';

const mocks = vi.hoisted(() => ({
  api: { upload: vi.fn() },
  apiFactory: vi.fn(),
  loadFont: vi.fn(),
  loadFonts: vi.fn(),
  rasterizeText: vi.fn(),
}));

vi.mock('@/shared/api/context', () => ({ useApi: () => mocks.apiFactory() }));
vi.mock('@/features/editor/text/fonts', () => ({ loadFont: mocks.loadFont, loadFonts: mocks.loadFonts }));
vi.mock('@/features/editor/text/rasterize', () => ({ rasterizeText: mocks.rasterizeText }));

afterEach(cleanup);
beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiFactory.mockReturnValue(mocks.api);
  mocks.loadFont.mockResolvedValue(true);
  mocks.loadFonts.mockResolvedValue([
    { family: 'Arial', styles: ['regular'], path: 'fonts/arial.ttf', bundled: false },
    { family: 'Inter', styles: ['regular', 'bold'], path: 'fonts/inter.ttf', bundled: true },
  ]);
  mocks.rasterizeText.mockResolvedValue({ blob: new Blob(['png'], { type: 'image/png' }), hash: 'a'.repeat(64), width: 90, height: 40 });
  mocks.api.upload.mockResolvedValue({ src: `media/text-title-${'a'.repeat(64)}.png` });
});

const clip: TextClip = {
  id: 'title-1', track: 'video', src: 'media/text-title-1-pending.png', raster: 'media/text-title-1-pending.png',
  media: 'text', src_in: 0, src_out: 5, start: 0, fade_in: 0, fade_out: 0, speed: 1,
  text: {
    content: 'Hola', font: 'Arial', weight: 700, size: 48, color: '#ffffff',
    stroke: { width: 2, color: '#000000' }, shadow: { x: 0, y: 3, blur: 8, color: '#00000099' },
    align: 'center', line_height: 1.2, max_width: 800,
  },
  transform: {
    x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
    crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
  },
  keyframes: {},
};

function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void; reject: (error: Error) => void } {
  let resolve = (_value: T): void => undefined;
  let reject = (_error: Error): void => undefined;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

describe('TextInspector', () => {
  it('adds a title using the default preset', () => {
    const onAdd = vi.fn();
    render(<TextInspector clip={null} path="/project.json" onAdd={onAdd} onChange={vi.fn()} onRasterChange={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: t('editor.text.add') }));

    expect(onAdd).toHaveBeenCalledWith('lower-third');
  });

  it('does not repeat the font effect when the API context returns a new client', () => {
    mocks.apiFactory.mockImplementation(() => ({ upload: vi.fn() }));
    render(<TextInspector clip={null} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);

    expect(mocks.apiFactory).toHaveBeenCalledOnce();
  });

  it('makes the selected preset draggable into the timeline', () => {
    render(<TextInspector clip={null} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);
    const dataTransfer = { setData: vi.fn(), effectAllowed: 'none' };

    fireEvent.dragStart(screen.getByRole('button', { name: t('editor.text.add') }), { dataTransfer });

    expect(dataTransfer.setData).toHaveBeenCalledWith('application/x-editor-text-preset', 'lower-third');
    expect(dataTransfer.effectAllowed).toBe('copy');
  });

  it('updates text and uploads the rasterized PNG with its content hash', async () => {
    const onChange = vi.fn();
    const onRasterChange = vi.fn();
    render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={onChange} onRasterChange={onRasterChange} />);

    fireEvent.change(screen.getByLabelText(t('editor.text.content')), { target: { value: 'Hola equipo' } });
    expect(onChange).toHaveBeenCalledWith('title-1', expect.objectContaining({ content: 'Hola equipo' }));
    await waitFor(() => expect(mocks.api.upload).toHaveBeenCalledWith(
      expect.stringContaining('sha256=' + 'a'.repeat(64)),
      expect.any(Blob),
      'image/png',
    ));
    await waitFor(() => expect(onRasterChange).toHaveBeenCalledWith('title-1', `media/text-title-${'a'.repeat(64)}.png`));
  });

  it('edits text styles and keeps numbers inside their supported ranges', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={onChange} onRasterChange={vi.fn()} />);

    fireEvent.change(screen.getByLabelText(t('editor.text.size')), { target: { value: '1200' } });
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ size: 1000 }));
    fireEvent.change(screen.getByLabelText(t('editor.text.size')), { target: { value: '' } });
    expect(onChange).toHaveBeenCalledTimes(1);

    fireEvent.change(screen.getByLabelText(t('editor.text.stroke_width')), { target: { value: '-2' } });
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ stroke: { width: 0, color: '#000000' } }));
    fireEvent.change(screen.getByLabelText(t('editor.text.shadow_blur')), { target: { value: '150' } });
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ shadow: { x: 0, y: 3, blur: 100, color: '#00000099' } }));
    fireEvent.change(screen.getByLabelText(t('editor.text.color')), { target: { value: '#ff0000' } });
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ color: '#ff0000' }));
    fireEvent.change(screen.getByLabelText(t('editor.text.stroke_color')), { target: { value: '#ff00ff' } });
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ stroke: { width: 2, color: '#ff00ff' } }));

    await user.click(await screen.findByRole('combobox', { name: t('editor.text.font') }));
    await user.click(await screen.findByRole('option', { name: 'Inter' }));
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ font: 'Inter' }));
    await user.click(await screen.findByRole('combobox', { name: t('editor.text.weight') }));
    await user.click(await screen.findByRole('option', { name: '800' }));
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ weight: 800 }));
    await user.click(await screen.findByRole('combobox', { name: t('editor.text.align') }));
    await user.click(await screen.findByRole('option', { name: t('editor.text.align_left') }));
    expect(onChange).toHaveBeenLastCalledWith('title-1', expect.objectContaining({ align: 'left' }));
  });

  it('shows an accessible error if the raster upload fails', async () => {
    mocks.api.upload.mockRejectedValue(new Error('offline'));
    render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);

    expect((await screen.findByRole('alert')).textContent).toContain(t('editor.text.error'));
  });

  it('reports a font-list failure while the selected title is still mounted', async () => {
    mocks.loadFonts.mockRejectedValue(new Error('offline'));
    mocks.rasterizeText.mockRejectedValue(new Error('canvas unavailable'));
    render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);

    expect((await screen.findByRole('alert')).textContent).toContain(t('editor.text.error'));
  });

  it('ignores a font-list response after the inspector unmounts', async () => {
    const fonts = deferred<EditorFont[]>();
    mocks.loadFonts.mockReturnValue(fonts.promise);
    const { unmount } = render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);
    await waitFor(() => expect(mocks.loadFonts).toHaveBeenCalledOnce());
    unmount();

    await act(async () => {
      fonts.resolve([]);
      await fonts.promise;
    });

    expect(mocks.loadFonts).toHaveBeenCalledOnce();
  });

  it('cancels a raster while a font is still loading after unmount', async () => {
    const font = deferred<boolean>();
    mocks.loadFont.mockReturnValue(font.promise);
    const { unmount } = render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);
    await waitFor(() => expect(mocks.loadFont).toHaveBeenCalledOnce());
    unmount();

    await act(async () => {
      font.resolve(true);
      await font.promise;
    });

    expect(mocks.rasterizeText).not.toHaveBeenCalled();
  });

  it('ignores a font-load rejection after unmount', async () => {
    const font = deferred<boolean>();
    mocks.loadFont.mockReturnValue(font.promise);
    const { unmount } = render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);
    await waitFor(() => expect(mocks.loadFont).toHaveBeenCalledOnce());
    unmount();

    await act(async () => {
      font.reject(new Error('offline'));
      await font.promise.catch(() => undefined);
      await Promise.resolve();
    });

    expect(mocks.rasterizeText).not.toHaveBeenCalled();
  });

  it('cancels an upload when rasterization finishes after unmount', async () => {
    const raster = deferred<{ blob: Blob; hash: string; width: number; height: number }>();
    mocks.rasterizeText.mockReturnValue(raster.promise);
    const { unmount } = render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={vi.fn()} />);
    await waitFor(() => expect(mocks.rasterizeText).toHaveBeenCalledOnce());
    unmount();

    await act(async () => {
      raster.resolve({ blob: new Blob(['png']), hash: 'b'.repeat(64), width: 90, height: 40 });
      await raster.promise;
    });

    expect(mocks.api.upload).not.toHaveBeenCalled();
  });

  it('does not commit a raster upload or show an error after unmount', async () => {
    const finishUpload = async (settle: (upload: ReturnType<typeof deferred<{ src: string }>>) => void): Promise<void> => {
      const upload = deferred<{ src: string }>();
      mocks.api.upload.mockReturnValue(upload.promise);
      const onRasterChange = vi.fn();
      const { unmount } = render(<TextInspector clip={clip} path="/project.json" onAdd={vi.fn()} onChange={vi.fn()} onRasterChange={onRasterChange} />);
      await waitFor(() => expect(mocks.api.upload).toHaveBeenCalled());
      unmount();
      await act(async () => {
        settle(upload);
        await Promise.resolve();
      });
      expect(onRasterChange).not.toHaveBeenCalled();
    };

    await finishUpload((upload) => upload.resolve({ src: 'media/text-title-hash.png' }));
  });
});

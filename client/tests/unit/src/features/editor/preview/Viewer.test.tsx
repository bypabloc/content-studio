import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Viewer } from '@/features/editor/preview/Viewer';
import type { Doc, VisualClip } from '@/features/editor/model/types';
import { t } from '@/shared/i18n/t';

const mocks = vi.hoisted(() => ({
  render: vi.fn(),
  destroy: vi.fn(),
  queryUrl: vi.fn(() => '/editor/projects/frame'),
  createCompositor: vi.fn(() => ({ render: vi.fn(), destroy: vi.fn() })),
  sources: { get: vi.fn() },
}));

vi.mock('@/shared/api/context', () => ({ useApi: () => ({ queryUrl: mocks.queryUrl }) }));
vi.mock('@/features/editor/preview/webgl', () => ({ createCompositor: mocks.createCompositor }));
vi.mock('@/features/editor/preview/useLayerSources', () => ({ useLayerSources: () => mocks.sources }));

afterEach(() => {
  cleanup();
  mocks.createCompositor.mockClear();
  mocks.sources.get.mockClear();
  mocks.queryUrl.mockClear();
  const compositor = mocks.createCompositor.mock.results.at(-1)?.value;
  compositor?.render.mockClear();
  compositor?.destroy.mockClear();
});

const visual: VisualClip = {
  id: 'logo', track: 'video', src: 'logo.png', src_in: 0, src_out: 4, start: 0, fade_in: 0, fade_out: 0,
  media: 'image',
  transform: {
    x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
    crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5,
  },
  keyframes: {},
};

const doc: Doc = {
  version: 2,
  name: 'demo',
  sample_rate: 48000,
  canvas: { width: 1280, height: 720, fps: 30, background: '#000000' },
  tracks: [{ id: 'video', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false }],
  clips: [visual],
  markers: [],
  transitions: [],
};

describe('Viewer', () => {
  function latestDoc(onPreviewDoc: ReturnType<typeof vi.fn>): Doc {
    const call = onPreviewDoc.mock.calls[onPreviewDoc.mock.calls.length - 1];
    if (!call) throw new Error('El visor no emitió un documento de vista previa');
    return call[0] as Doc;
  }

  it('muestra el lienzo, las guias y dibuja con el compositor en el tiempo actual', () => {
    const { unmount } = render(<Viewer doc={doc} path="/project.json" time={1} selectedClipId="logo" onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);

    const canvas = screen.getByLabelText(t('editor.viewer.canvas'));
    expect(canvas.tagName).toBe('CANVAS');
    expect(screen.getByRole('img', { name: t('editor.viewer.safe_area') })).toBeTruthy();
    expect(mocks.createCompositor).toHaveBeenCalledWith(canvas);
    expect(mocks.createCompositor.mock.results.at(-1)?.value.render).toHaveBeenCalledWith(doc, 1, mocks.sources);

    unmount();
    expect(mocks.createCompositor.mock.results.at(-1)?.value.destroy).toHaveBeenCalledOnce();
  });

  it('mueve el clip con las asas y confirma una sola edicion al soltar', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    render(<Viewer doc={doc} path="/project.json" time={1} selectedClipId="logo" onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} />);
    const stage = screen.getByRole('group', { name: t('editor.viewer.stage') });
    vi.spyOn(stage, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 0, left: 0, top: 0, right: 1280, bottom: 720, width: 1280, height: 720,
      toJSON: () => ({}),
    });
    const move = screen.getByRole('button', { name: t('editor.viewer.move') });
    fireEvent.pointerDown(move, { pointerId: 3, clientX: 100, clientY: 100, button: 0 });
    fireEvent.pointerMove(move, { pointerId: 3, clientX: 228, clientY: 172 });
    fireEvent.pointerUp(move, { pointerId: 3, clientX: 228, clientY: 172 });

    const edited = onPreviewDoc.mock.calls.at(-1)?.[0] as Doc;
    expect((edited.clips[0] as VisualClip).transform).toMatchObject({ x: 128, y: 72 });
    expect(onCommitPreview).toHaveBeenCalledOnce();
  });

  it('solicita al server el fotograma exacto del proyecto en el tiempo del cabezal', () => {
    render(<Viewer doc={doc} path="/project.json" time={1.25} selectedClipId="logo" onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: t('editor.viewer.exact_frame') }));

    expect(mocks.queryUrl).toHaveBeenCalledWith('/editor/projects/frame', { path: '/project.json', t: '1.25' });
    expect(screen.getByRole('img', { name: t('editor.viewer.exact_frame_image', { time: '1.25' }) })).toBeTruthy();
  });

  it('escala proporcionalmente, rota, recorta y puede cancelar una transformación', () => {
    const onPreviewDoc = vi.fn();
    const onCommitPreview = vi.fn();
    const onCancelPreview = vi.fn();
    const { rerender } = render(
      <Viewer doc={doc} path="/project.json" time={1} selectedClipId="logo" onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} onCancelPreview={onCancelPreview} />,
    );
    const stage = screen.getByRole('group', { name: t('editor.viewer.stage') });
    vi.spyOn(stage, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 0, left: 0, top: 0, right: 1280, bottom: 720, width: 1280, height: 720,
      toJSON: () => ({}),
    });

    const scale = screen.getByRole('button', { name: t('editor.viewer.scale') });
    fireEvent.pointerDown(scale, { pointerId: 20, clientX: 0, clientY: 0, button: 0 });
    fireEvent.pointerMove(scale, { pointerId: 20, clientX: 128, clientY: 72, shiftKey: true });
    fireEvent.pointerUp(scale, { pointerId: 20, clientX: 128, clientY: 72, shiftKey: true });
    expect(latestDoc(onPreviewDoc).clips[0]).toMatchObject({ transform: { scale_x: 1.1, scale_y: 1.1 } });

    const rotate = screen.getByRole('button', { name: t('editor.viewer.rotate') });
    fireEvent.pointerDown(rotate, { pointerId: 21, clientX: 700, clientY: 360, button: 0 });
    fireEvent.pointerMove(rotate, { pointerId: 21, clientX: 640, clientY: 420 });
    fireEvent.pointerUp(rotate, { pointerId: 21, clientX: 640, clientY: 420 });
    expect((latestDoc(onPreviewDoc).clips[0] as VisualClip).transform.rotation).toBeCloseTo(90);

    const cropped = structuredClone(doc);
    (cropped.clips[0] as VisualClip).transform.crop.r = 0.5;
    rerender(
      <Viewer doc={cropped} path="/project.json" time={1} selectedClipId="logo" onPreviewDoc={onPreviewDoc} onCommitPreview={onCommitPreview} onCancelPreview={onCancelPreview} />,
    );
    const crop = screen.getByRole('button', { name: t('editor.viewer.crop') });
    fireEvent.pointerDown(crop, { pointerId: 22, clientX: 0, clientY: 0, button: 0 });
    fireEvent.pointerMove(crop, { pointerId: 22, clientX: 128, clientY: 0 });
    expect((latestDoc(onPreviewDoc).clips[0] as VisualClip).transform.crop.l).toBeCloseTo(0.1);
    fireEvent.pointerCancel(crop, { pointerId: 22 });
    expect(onCancelPreview).toHaveBeenCalledOnce();
    expect(onCommitPreview).toHaveBeenCalledTimes(2);
  });

  it('muestra un error recuperable cuando WebGL no está disponible', async () => {
    mocks.createCompositor.mockImplementationOnce(() => { throw new Error('WebGL unavailable'); });
    render(<Viewer doc={doc} path="/project.json" time={0} selectedClipId={null} onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);

    expect(await screen.findByText(t('editor.viewer.webgl_error'))).toBeTruthy();
  });

  it('actualiza el compositor al cargar un video y una imagen fuente', async () => {
    const compositor = { render: vi.fn(), destroy: vi.fn() };
    mocks.createCompositor.mockReturnValue(compositor);
    const video = document.createElement('video');
    mocks.sources.get.mockReturnValue(video);
    const { rerender } = render(<Viewer doc={doc} path="/video-project.json" time={0} selectedClipId="logo" onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);

    act(() => video.dispatchEvent(new Event('loadeddata')));
    await waitFor(() => expect(compositor.render).toHaveBeenCalledTimes(2));

    const image = document.createElement('img');
    mocks.sources.get.mockReturnValue(image);
    rerender(<Viewer doc={doc} path="/image-project.json" time={0} selectedClipId="logo" onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);
    act(() => image.dispatchEvent(new Event('load')));
    await waitFor(() => expect(compositor.render).toHaveBeenCalledTimes(3));
  });

  it('oculta el fotograma exacto al alternar el control y bloquea asas de pistas protegidas', () => {
    const lockedDoc = structuredClone(doc);
    lockedDoc.tracks[0].locked = true;
    render(<Viewer doc={lockedDoc} path="/project.json" time={1} selectedClipId="logo" onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);
    const exact = screen.getByRole('button', { name: t('editor.viewer.exact_frame') });
    fireEvent.click(exact);
    expect(screen.getByRole('img', { name: t('editor.viewer.exact_frame_image', { time: '1.00' }) })).toBeTruthy();
    fireEvent.click(exact);
    expect(screen.queryByRole('img', { name: t('editor.viewer.exact_frame_image', { time: '1.00' }) })).toBeNull();
    expect(screen.getByRole('button', { name: t('editor.viewer.move') }).hasAttribute('disabled')).toBe(true);
  });

  it('usa el tamaño del lienzo si el stage no tiene dimensiones y activa recorte con Alt', () => {
    const onPreviewDoc = vi.fn();
    render(<Viewer doc={doc} path="/project.json" time={1} selectedClipId="logo" onPreviewDoc={onPreviewDoc} onCommitPreview={vi.fn()} />);
    const stage = screen.getByRole('group', { name: t('editor.viewer.stage') });
    vi.spyOn(stage, 'getBoundingClientRect').mockReturnValue({
      x: 0, y: 0, left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0,
      toJSON: () => ({}),
    });
    const move = screen.getByRole('button', { name: t('editor.viewer.move') });
    fireEvent.pointerDown(move, { pointerId: 23, clientX: 0, clientY: 0, button: 0, altKey: true });
    fireEvent.pointerMove(move, { pointerId: 23, clientX: 128, clientY: 0 });
    const edited = latestDoc(onPreviewDoc);
    expect((edited.clips[0] as VisualClip).transform.crop.l).toBeCloseTo(0.1);
  });

  it('usa el bloqueo predeterminado si la pista visual ya no existe', () => {
    const orphan = structuredClone(doc);
    orphan.tracks = [];
    render(<Viewer doc={orphan} path="/project.json" time={0} selectedClipId="logo" onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);
    expect(screen.getByRole('button', { name: t('editor.viewer.move') }).hasAttribute('disabled')).toBe(true);
  });

  it('ignora un movimiento cancelado antes de arrastrar cuando el callback es opcional', () => {
    render(<Viewer doc={doc} path="/project.json" time={0} selectedClipId="logo" onPreviewDoc={vi.fn()} onCommitPreview={vi.fn()} />);
    const move = screen.getByRole('button', { name: t('editor.viewer.move') });
    fireEvent.pointerDown(move, { pointerId: 24, clientX: 0, clientY: 0, button: 0 });
    fireEvent.pointerCancel(move, { pointerId: 24 });
  });
});

import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useLayerSources } from '@/features/editor/preview/useLayerSources';
import type { Api } from '@/shared/api/client';
import type { Canvas, Doc, TextClip, VideoTrack, VisualClip } from '@/features/editor/model/types';

const canvas: Canvas = { width: 1280, height: 720, fps: 30, background: '#000000' };
const track: VideoTrack = { id: 'v1', kind: 'video', name: 'Video', opacity: 1, hidden: false, locked: false };

function doc(source = 'media.mp4'): Doc {
  const clip: VisualClip = {
    id: 'clip', track: 'v1', src: source, src_in: 0, src_out: 4, start: 0, fade_in: 0, fade_out: 0,
    media: source.endsWith('.png') ? 'image' : 'video',
    transform: { x: 0, y: 0, scale_x: 1, scale_y: 1, rotation: 0, opacity: 1,
      crop: { l: 0, t: 0, r: 0, b: 0 }, anchor_x: 0.5, anchor_y: 0.5 },
    keyframes: {},
  };
  return { version: 2, name: 'preview', sample_rate: 48000, canvas, tracks: [track], clips: [clip], markers: [], transitions: [] };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('fuentes de capas del compositor', () => {
  it('crea fuentes de video e imagen con la ruta del proyecto y limpia los videos', () => {
    const pause = vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
    const load = vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => undefined);
    const api = { queryUrl: vi.fn((_path: string, query: Record<string, string>) => '/preview?' + query.source) } as unknown as Api;
    const initialDoc = doc();
    const { result, unmount } = renderHook(() => useLayerSources(initialDoc, '/project/project.json', api));

    expect(result.current.get('clip')).toBeInstanceOf(HTMLVideoElement);
    expect((result.current.get('clip') as HTMLVideoElement).crossOrigin).toBe('anonymous');
    expect(api.queryUrl).toHaveBeenCalledWith('/editor/projects/media', { path: '/project/project.json', source: 'media.mp4' });
    unmount();
    expect(pause).toHaveBeenCalledOnce();
    expect(load).toHaveBeenCalledOnce();
  });

  it('usa una imagen para clips fijos y reconstruye fuentes si cambia el proyecto', () => {
    const api = { queryUrl: vi.fn((_path: string, query: Record<string, string>) => '/preview?' + query.source) } as unknown as Api;
    const { result, rerender, unmount } = renderHook(({ model }) => useLayerSources(model, '/project/project.json', api), {
      initialProps: { model: doc('logo.png') },
    });
    expect(result.current.get('clip')).toBeInstanceOf(HTMLImageElement);
    expect((result.current.get('clip') as HTMLImageElement).crossOrigin).toBe('anonymous');
    const initial = result.current.get('clip');
    vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => undefined);
    vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => undefined);

    act(() => rerender({ model: doc('replacement.mp4') }));

    expect(result.current.get('clip')).toBeInstanceOf(HTMLVideoElement);
    expect(result.current.get('clip')).not.toBe(initial);
    unmount();
  });

  it('carga el PNG rasterizado de un clip de texto como una imagen', () => {
    const api = { queryUrl: vi.fn((_path: string, query: Record<string, string>) => '/preview?' + query.source) } as unknown as Api;
    const initial = doc();
    const image = initial.clips[0] as VisualClip;
    const title: TextClip = {
      ...image,
      id: 'title',
      src: 'media/text-title-hash.png',
      media: 'text',
      raster: 'media/text-title-hash.png',
      text: {
        content: 'Hola', font: 'Arial', weight: 700, size: 48, color: '#ffffff',
        stroke: { width: 2, color: '#000000' }, shadow: { x: 0, y: 2, blur: 4, color: '#000000' },
        align: 'center', line_height: 1.2, max_width: 800,
      },
    };
    const model = { ...initial, version: 3 as const, clips: [title] };
    const { result, unmount } = renderHook(() => useLayerSources(model, '/project/project.json', api));

    expect(result.current.get('title')).toBeInstanceOf(HTMLImageElement);
    expect(api.queryUrl).toHaveBeenCalledWith('/editor/projects/media', {
      path: '/project/project.json', source: 'media/text-title-hash.png',
    });
    unmount();
  });

  it('conserva la fuente cuando solo cambia la transformacion del clip', () => {
    const api = { queryUrl: vi.fn(() => '/preview') } as unknown as Api;
    const initial = doc();
    const { result, rerender } = renderHook(({ model }) => useLayerSources(model, '/project/project.json', api), {
      initialProps: { model: initial },
    });
    const source = result.current.get('clip');
    const clip = initial.clips[0] as VisualClip;

    act(() => rerender({ model: { ...initial, clips: [{ ...clip, transform: { ...clip.transform, x: 120 } }] } }));

    expect(result.current.get('clip')).toBe(source);
    expect(api.queryUrl).toHaveBeenCalledOnce();
  });
});

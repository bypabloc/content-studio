import { useEffect, useMemo } from 'react';

import type { Api } from '@/shared/api/client';

import type { Doc, VisualClip } from '../model/types';

export type LayerSource = HTMLVideoElement | HTMLImageElement;
export type LayerSourceLookup = Pick<ReadonlyMap<string, LayerSource>, 'get'>;

export class LayerSourceStore implements LayerSourceLookup {
  private sources = new Map<string, LayerSource>();

  get(id: string): LayerSource | undefined {
    return this.sources.get(id);
  }

  replace(sources: Map<string, LayerSource>): void {
    this.sources = sources;
  }
}

function sourceUrl(api: Api, projectPath: string, clip: VisualClip): string {
  return api.queryUrl('/editor/projects/media', { path: projectPath, source: clip.src });
}

function createSource(clip: VisualClip): LayerSource {
  if (clip.media === 'image' || clip.media === 'text') {
    const image = new Image();
    image.decoding = 'async';
    image.crossOrigin = 'anonymous';
    return image;
  }
  const video = document.createElement('video');
  video.crossOrigin = 'anonymous';
  video.muted = true;
  video.playsInline = true;
  video.preload = 'auto';
  return video;
}

/** Mantiene una sola fuente silenciosa por clip visual y libera los medios al cambiar de proyecto. */
export function useLayerSources(doc: Doc, projectPath: string, api: Api): LayerSourceStore {
  const sources = useMemo(() => new LayerSourceStore(), []);
  const sourceSignature = JSON.stringify(
    doc.clips.flatMap((clip) =>
      clip.media === 'video' || clip.media === 'image' || clip.media === 'text' ? [[clip.id, clip.media, clip.src]] : [],
    ),
  );

  useEffect(() => {
    const next = new Map<string, LayerSource>();
    for (const clip of doc.clips) {
      if (clip.media !== 'video' && clip.media !== 'image' && clip.media !== 'text') continue;
      const source = createSource(clip);
      source.src = sourceUrl(api, projectPath, clip);
      next.set(clip.id, source);
    }
    sources.replace(next);
    return () => {
      for (const source of next.values()) {
        if (source instanceof HTMLVideoElement) {
          source.pause();
          source.removeAttribute('src');
          source.load();
        } else {
          source.src = '';
        }
      }
      sources.replace(new Map());
    };
    // Transform edits replace `doc.clips` but do not require new media elements.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, projectPath, sourceSignature, sources]);

  return sources;
}

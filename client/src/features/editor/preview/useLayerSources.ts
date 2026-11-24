import { useEffect, useMemo, useState } from 'react';

import type { Api } from '@/shared/api/client';

import type { Clip, Doc, VisualClip } from '../model/types';
import { parseCube, type Lut3D } from './lut';

export type LayerSource = HTMLVideoElement | HTMLImageElement;
export type LayerSourceLookup = Pick<ReadonlyMap<string, LayerSource>, 'get'> & {
  getLut?: (path: string) => Lut3D | undefined;
};

export class LayerSourceStore implements LayerSourceLookup {
  private sources = new Map<string, LayerSource>();
  private luts = new Map<string, Lut3D>();

  get(id: string): LayerSource | undefined {
    return this.sources.get(id);
  }

  getLut(path: string): Lut3D | undefined {
    return this.luts.get(path);
  }

  replace(sources: Map<string, LayerSource>, luts = new Map<string, Lut3D>()): void {
    this.sources = sources;
    this.luts = luts;
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

function isVisualClip(clip: Clip): clip is VisualClip {
  return clip.media === 'video' || clip.media === 'image' || clip.media === 'text';
}

/** Mantiene una sola fuente silenciosa por clip visual y libera los medios al cambiar de proyecto. */
export function useLayerSources(doc: Doc, projectPath: string, api: Api): LayerSourceStore {
  const sources = useMemo(() => new LayerSourceStore(), []);
  const [, setLutRevision] = useState(0);
  const visualClips = doc.clips.filter(isVisualClip);
  const sourceSignature = JSON.stringify(visualClips.map((clip) => [clip.id, clip.media, clip.src, clip.color?.lut ?? '']));

  useEffect(() => {
    let active = true;
    const next = new Map<string, LayerSource>();
    const luts = new Map<string, Lut3D>();
    for (const clip of visualClips) {
      const source = createSource(clip);
      source.src = sourceUrl(api, projectPath, clip);
      next.set(clip.id, source);
    }
    const lutPaths = [...new Set(visualClips.flatMap((clip) => clip.color?.lut ? [clip.color.lut] : []))];
    sources.replace(next, luts);
    void Promise.all(lutPaths.map(async (lutPath) => {
      try {
        const response = await fetch(api.queryUrl('/editor/projects/luts', { path: projectPath, source: lutPath }));
        if (response.ok) luts.set(lutPath, parseCube(await response.text()));
      } catch {
        return;
      }
    })).then(() => {
      if (active) {
        sources.replace(next, luts);
        setLutRevision((revision) => revision + 1);
      }
    });
    return () => {
      active = false;
      for (const source of next.values()) {
        if (source instanceof HTMLVideoElement) {
          source.pause();
          source.removeAttribute('src');
          source.load();
        } else {
          source.src = '';
        }
      }
      sources.replace(new Map(), new Map());
    };
    // Transform edits replace `doc.clips` but do not require new media elements.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, projectPath, sourceSignature, sources]);

  return sources;
}

import { useEffect, useRef, useState } from 'react';
import type JASSUB from 'jassub';

import { useApi } from '@/shared/api/context';
import { UICanvas } from '@/shared/components/atoms/UICanvas';

import { type DocIn, type StyleIn, toAss } from '@/features/subtitles/ass';
import { BUILTIN_PRESETS } from '@/features/subtitles/presets';
import type { SubtitleTrack as SubtitleTrackModel } from './model/types';

type SubtitleDocument = DocIn & { version: number; style?: Partial<StyleIn> };

/** Lienzo transparente de JASSUB sincronizado con el tiempo global del cabezal. */
export function SubtitleTrack({
  track,
  time,
  width,
  height,
}: {
  track: SubtitleTrackModel;
  time: number;
  width: number;
  height: number;
}): React.JSX.Element {
  const api = useApi();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<JASSUB | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = width;
    canvas.height = height;
    let active = true;
    let instance: JASSUB | null = null;
    setReady(false);
    void api
      .get<SubtitleDocument>(`/subtitles/${encodeURIComponent(track.subtitles_project)}`)
      .then(async (document) => {
        const style = Object.keys(document.style ?? {}).length
          ? { ...BUILTIN_PRESETS.classic, ...document.style }
          : BUILTIN_PRESETS.classic;
        const ass = toAss(document, style, [width, height]);
        const { default: JassubCtor } = await import('jassub');
        if (!active) return;
        instance = new JassubCtor({ canvas, subContent: ass });
        rendererRef.current = instance;
        await instance.ready;
        if (!active) return;
        setReady(true);
      })
      .catch(() => undefined);
    return () => {
      active = false;
      rendererRef.current = null;
      if (instance) void instance.destroy();
    };
  }, [api, height, track.subtitles_project, width]);

  useEffect(() => {
    if (!ready) return;
    rendererRef.current?.manualRender({
      expectedDisplayTime: performance.now(),
      width,
      height,
      mediaTime: time,
    });
  }, [height, ready, time, width]);

  return (
    <UICanvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 size-full"
      data-subtitle-track={track.id}
    />
  );
}

import { useEffect, useRef, useState } from 'react';
import type JASSUB from 'jassub';

import { UIStack } from '@/shared/components/atoms/UIStack';
import { UIMedia } from '@/shared/components/atoms/UIMedia';

import { SafeZones, type ZoneName } from './SafeZones';

/**
 * La vista previa (D-9): el video con el ASS dibujado por JASSUB. El paquete entra con import diferido, para no pesar en
 * el arranque (client/budget.json). Las zonas seguras van encima del video.
 */
export function SubtitlesPreview({
  src,
  ass,
  zone,
  onAspect,
}: {
  src: string;
  ass: string;
  zone: ZoneName | null;
  onAspect: (aspect: number) => void;
}): React.JSX.Element {
  const [media, setMedia] = useState<HTMLMediaElement | null>(null);
  const renderer = useRef<JASSUB | null>(null);
  const subtitles = useRef(ass);
  // Un callback nuevo en cada render no debe recrear JASSUB: se lee desde una referencia.
  const aspectListener = useRef(onAspect);

  useEffect(() => {
    aspectListener.current = onAspect;
  }, [onAspect]);

  useEffect(() => {
    subtitles.current = ass;
    // JASSUB asigna `renderer` cuando su worker está listo; antes, la pista más reciente va al crear la instancia (abajo).
    if (renderer.current?.renderer) void renderer.current.renderer.setTrack(ass);
  }, [ass]);

  useEffect(() => {
    if (!(media instanceof HTMLVideoElement)) return;
    const video = media;
    let active = true;
    const measure = () => {
      if (video.videoHeight > 0) aspectListener.current(video.videoWidth / video.videoHeight);
    };
    video.addEventListener('loadedmetadata', measure);
    void import('jassub').then(({ default: JassubCtor }) => {
      if (!active) return;
      const instance = new JassubCtor({ video, subContent: subtitles.current });
      renderer.current = instance;
      // Con el worker listo se manda la pista más reciente. Sin WebGL, la vista previa queda vacía sin romper el editor.
      void instance.ready
        .then(() => instance.renderer.setTrack(subtitles.current))
        .catch(() => undefined);
    });
    return () => {
      active = false;
      video.removeEventListener('loadedmetadata', measure);
      void renderer.current?.destroy();
      renderer.current = null;
    };
  }, [media]);

  return (
    <UIStack className="relative overflow-hidden rounded-xl bg-black">
      <UIMedia kind="video" src={src} className="block w-full" mediaRef={setMedia} />
      <SafeZones zone={zone} />
    </UIStack>
  );
}

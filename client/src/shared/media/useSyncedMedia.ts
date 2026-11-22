import { useCallback, useEffect, useRef, useState } from 'react';

/** Lo que la pantalla necesita de un medio: su tiempo, si suena y cómo moverlo. */
export interface SyncedMedia {
  time: number;
  playing: boolean;
  seek: (seconds: number) => void;
  toggle: () => void;
}

// Mueve el medio a un tiempo. Es la única escritura sobre el elemento: el resto del hook solo lee.
function moveTo(element: HTMLMediaElement, seconds: number): void {
  element.currentTime = seconds;
}

/**
 * Sigue un `<video>` o `<audio>`: el tiempo y si suena. Con `skip`, un tiempo que cae dentro de un tramo cortado salta
 * a su final (la vista previa «Escuchar sin cortes»). La onda sigue sola al usar el mismo medio (`media` de WaveSurfer).
 */
export function useSyncedMedia(media: HTMLMediaElement | null, skip?: (seconds: number) => number | null): SyncedMedia {
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const skipRef = useRef(skip);

  useEffect(() => {
    skipRef.current = skip;
  });

  useEffect(() => {
    if (!media) return;
    const onTime = () => {
      const target = skipRef.current?.(media.currentTime) ?? null;
      if (target !== null) moveTo(media, target);
      setTime(media.currentTime);
    };
    const onPlay = () => setPlaying(true);
    const onStop = () => setPlaying(false);
    media.addEventListener('timeupdate', onTime);
    media.addEventListener('play', onPlay);
    media.addEventListener('pause', onStop);
    media.addEventListener('ended', onStop);
    return () => {
      media.removeEventListener('timeupdate', onTime);
      media.removeEventListener('play', onPlay);
      media.removeEventListener('pause', onStop);
      media.removeEventListener('ended', onStop);
    };
  }, [media]);

  const seek = useCallback(
    (seconds: number) => {
      if (!media) return;
      moveTo(media, seconds);
      setTime(seconds);
    },
    [media],
  );

  const toggle = useCallback(() => {
    if (!media) return;
    if (media.paused) void media.play();
    else media.pause();
  }, [media]);

  return { time, playing, seek, toggle };
}

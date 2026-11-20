import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { UIButton } from '@/shared/components/atoms/UIButton';
import { UIStack } from '@/shared/components/atoms/UIStack';
import { t } from '@/shared/i18n/t';

// En un campo de texto el espacio es una letra: ahí no reproduce.
function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName));
}

// Las pistas en pantalla: cuando una empieza a sonar, las demás se pausan (Comparar, AC-10).
const tracks = new Set<WaveSurfer>();
// La pista que el usuario tocó por último: Espacio la controla, y ninguna otra (AC-10 también con teclado).
let active: WaveSurfer | null = null;

/**
 * Un audio con su forma de onda y su botón. La onda usa los picos que calcula el server: wavesurfer.js no decodifica el
 * audio en el WebView. Espacio reproduce o pausa la pista tocada por último, salvo al escribir (AC-8).
 */
export function Player({ src, peaks }: { src: string; peaks: number[] }) {
  const container = useRef<HTMLDivElement>(null);
  const wave = useRef<WaveSurfer | null>(null);
  const [playing, setPlaying] = useState(false);
  const takeOver = () => {
    active = wave.current;
  };

  useEffect(() => {
    if (!container.current) return;
    const instance = WaveSurfer.create({
      container: container.current,
      url: src,
      peaks: [peaks],
      height: 64,
      waveColor: 'oklch(0.705 0.015 286)',
      progressColor: 'oklch(0.541 0.281 293)',
      normalize: true,
    });
    tracks.add(instance);
    instance.on('play', () => {
      setPlaying(true);
      for (const other of tracks) {
        if (other !== instance) other.pause();
      }
    });
    instance.on('pause', () => setPlaying(false));
    wave.current = instance;
    return () => {
      tracks.delete(instance);
      if (active === instance) active = null;
      instance.destroy();
      wave.current = null;
    };
  }, [src, peaks]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      // El botón reproduce con su propio clic al pulsar Espacio; en un campo de texto el espacio es una letra.
      if (event.key !== ' ' || isTyping(event.target) || event.target instanceof HTMLButtonElement) return;
      if (!wave.current || active !== wave.current) return;
      event.preventDefault();
      void wave.current.playPause();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <UIStack direction="row" align="center" gap="sm" onPointerDown={takeOver} onFocus={takeOver}>
      <UIButton
        variant="primary"
        icon={playing ? 'pause' : 'play'}
        aria-label={playing ? t('player.pause') : t('player.play')}
        onClick={() => void wave.current?.playPause()}
        className="size-11 shrink-0 rounded-full px-0"
      />
      <UIStack ref={container} className="min-w-0 flex-1" />
    </UIStack>
  );
}

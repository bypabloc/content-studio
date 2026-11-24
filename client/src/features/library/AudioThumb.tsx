import { useEffect, useRef } from 'react';

import { UICanvas } from '@/shared/components/atoms/UICanvas';
import { useMediaPeaks } from '@/shared/media/useMediaInfo';

const WIDTH = 240;
const HEIGHT = 64;

/** La onda chica de un audio (D-1): 200 picos de `/media/peaks` dibujados en un canvas; la base no guarda imágenes. */
export function AudioThumb({ path, label }: { path: string; label: string }): React.JSX.Element {
  const peaks = useMediaPeaks(path, 200);
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const context = canvas.current?.getContext('2d');
    const values = peaks.data?.peaks;
    if (!context || !values) return;
    context.clearRect(0, 0, WIDTH, HEIGHT);
    context.fillStyle = getComputedStyle(canvas.current as HTMLCanvasElement).color;
    const step = WIDTH / values.length;
    values.forEach((value, index) => {
      const bar = Math.max(1, value * HEIGHT);
      context.fillRect(index * step, (HEIGHT - bar) / 2, Math.max(1, step - 1), bar);
    });
  }, [peaks.data]);
  return <UICanvas ref={canvas} width={WIDTH} height={HEIGHT} role="img" aria-label={label} className="h-16 w-full text-primary" />;
}

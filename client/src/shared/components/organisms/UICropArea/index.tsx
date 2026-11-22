import { type PointerEvent, useRef } from 'react';

import { UIBox } from '../../atoms/UIBox';
import { UIRemoteImage } from '../../molecules/UIRemoteImage';

/** Un rectángulo en coordenadas normalizadas del cuadro (0 a 1): origen arriba a la izquierda. */
export interface CropRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

type Props = {
  /** Nombre accesible de la zona (la imagen y el rectángulo). */
  label: string;
  src: string;
  alt: string;
  width: number;
  height: number;
  rect: CropRect;
  onChange: (rect: CropRect) => void;
  errorText: string;
  retryLabel: string;
  onRetry?: () => void;
};

function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high);
}

/**
 * Una imagen con un rectángulo que se arrastra por ella (el encuadre manual de Convertir). El rectángulo conserva su
 * tamaño y solo se mueve, dentro del cuadro. Los puntos se leen en píxeles y se pasan a fracciones de la zona.
 *
 * @author Pablo Contreras
 * @since 2026/11/22
 */
export function UICropArea({
  label,
  src,
  alt,
  width,
  height,
  rect,
  onChange,
  errorText,
  retryLabel,
  onRetry,
}: Props): React.JSX.Element {
  const grip = useRef<{ x: number; y: number; origin: CropRect } | null>(null);

  const begin = (event: PointerEvent<HTMLElement>) => {
    grip.current = { x: event.clientX, y: event.clientY, origin: rect };
  };

  const move = (event: PointerEvent<HTMLElement>) => {
    const start = grip.current;
    if (!start) return;
    const box = event.currentTarget.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) return;
    onChange({
      ...start.origin,
      x: clamp(start.origin.x + (event.clientX - start.x) / box.width, 0, 1 - start.origin.w),
      y: clamp(start.origin.y + (event.clientY - start.y) / box.height, 0, 1 - start.origin.h),
    });
  };

  const end = () => {
    grip.current = null;
  };

  return (
    <UIBox
      role="group"
      aria-label={label}
      onPointerMove={move}
      onPointerUp={end}
      onPointerLeave={end}
      className="relative touch-none select-none overflow-hidden rounded-xl"
    >
      <UIRemoteImage
        src={src}
        alt={alt}
        width={width}
        height={height}
        errorText={errorText}
        retryLabel={retryLabel}
        onRetry={onRetry}
        className="block w-full"
      />
      <UIBox
        data-testid="crop-rect"
        onPointerDown={begin}
        className="absolute cursor-move border-2 border-primary bg-primary/10"
        style={{
          left: `${rect.x * 100}%`,
          top: `${rect.y * 100}%`,
          width: `${rect.w * 100}%`,
          height: `${rect.h * 100}%`,
        }}
      />
    </UIBox>
  );
}

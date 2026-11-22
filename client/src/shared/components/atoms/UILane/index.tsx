import { cn } from 'cn';
import type { ComponentProps } from 'react';

/** Pista de la línea de tiempo: crea el contexto relativo para posicionar sus clips. */
export function UILane({ className, style, ...props }: ComponentProps<'div'>): React.JSX.Element {
  return (
    <div
      className={cn('relative min-h-20 border-b border-border', className)}
      style={{ ...style, position: 'relative' }}
      {...props}
    />
  );
}

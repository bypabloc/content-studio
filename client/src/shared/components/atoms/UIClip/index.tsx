import { cn } from 'cn';
import type { ComponentProps } from 'react';

/** Clip interactivo, posicionado sobre una `UILane`; las dimensiones las define el tiempo y el zoom. */
export function UIClip({ className, style, type = 'button', ...props }: ComponentProps<'button'>): React.JSX.Element {
  return (
    <button
      type={type}
      className={cn('absolute top-2 h-16 min-w-2 overflow-hidden rounded-md border border-primary bg-primary/20 text-left text-foreground focus-visible:ui-focus', className)}
      style={{ ...style, position: 'absolute' }}
      {...props}
    />
  );
}

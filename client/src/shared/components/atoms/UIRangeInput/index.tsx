import { cn } from 'cn';
import type { ComponentProps } from 'react';

type Props = Omit<ComponentProps<'input'>, 'type' | 'value' | 'onChange' | 'aria-label'> & {
  label: string;
  value: number;
  onValueChange: (value: number) => void;
};

/** Control de rango accesible para valores continuos como el volumen de una pista. */
export function UIRangeInput({ label, value, onValueChange, className, ...props }: Props): React.JSX.Element {
  return (
    <input
      type="range"
      aria-label={label}
      value={value}
      onChange={(event) => onValueChange(Number(event.currentTarget.value))}
      className={cn('h-6 w-full cursor-pointer accent-primary focus-visible:ui-focus', className)}
      {...props}
    />
  );
}

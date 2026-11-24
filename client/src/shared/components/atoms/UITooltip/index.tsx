import type { ReactElement, ReactNode } from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/components/shadcn/tooltip';

// Demora al pasar el ratón; con el foco del teclado el texto aparece al instante.
const HOVER_DELAY_MS = 400;

type Props = { content: ReactNode; shortcut?: string; children: ReactElement };

/**
 * Texto de ayuda sobre un control: aparece al pasar el ratón tras una demora y al enfocar el control, y Escape lo
 * cierra. `shortcut` muestra el atajo de teclado junto al texto (spec 008, D-3).
 */
export function UITooltip({ content, shortcut, children }: Props): React.JSX.Element {
  return (
    <TooltipProvider delay={HOVER_DELAY_MS}>
      <Tooltip>
        <TooltipTrigger render={children} />
        <TooltipContent role="tooltip">
          {content}
          {shortcut ? <kbd className="rounded-sm bg-background/15 px-1 font-mono text-[0.7rem]">{shortcut}</kbd> : null}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

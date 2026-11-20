import type { FloatingToolbarPlacement } from './types'

export const HIDE_DELAY_MS = 2000
export const TOOLTIP_DELAY_MS = 200

export const PLACEMENT_CLASSES: Record<
  FloatingToolbarPlacement,
  {
    root: string
    hidden: string
    handle: string
    orientation: 'horizontal' | 'vertical'
    popupSide: 'top' | 'right' | 'bottom' | 'left'
    popupAlign: 'start' | 'center' | 'end'
    tooltipSide: 'top' | 'right' | 'bottom' | 'left'
  }
> = {
  'top-left': {
    root: 'top-4 left-4',
    hidden: '-translate-y-[calc(100%+1rem)]',
    handle: '-top-4 -left-4',
    orientation: 'horizontal',
    popupSide: 'bottom',
    popupAlign: 'start',
    tooltipSide: 'bottom',
  },
  top: {
    root: 'top-4 left-1/2 -translate-x-1/2',
    hidden: '-translate-y-[calc(100%+1rem)]',
    handle: '-top-4 left-1/2 -translate-x-1/2',
    orientation: 'horizontal',
    popupSide: 'bottom',
    popupAlign: 'center',
    tooltipSide: 'bottom',
  },
  'top-right': {
    root: 'top-4 right-4',
    hidden: '-translate-y-[calc(100%+1rem)]',
    handle: '-top-4 -right-4',
    orientation: 'horizontal',
    popupSide: 'bottom',
    popupAlign: 'end',
    tooltipSide: 'bottom',
  },
  left: {
    root: 'left-4 top-1/2 -translate-y-1/2',
    hidden: '-translate-x-[calc(100%+1rem)]',
    handle: '-left-4 top-1/2 -translate-y-1/2',
    orientation: 'vertical',
    popupSide: 'right',
    popupAlign: 'center',
    tooltipSide: 'right',
  },
  right: {
    root: 'right-4 top-1/2 -translate-y-1/2',
    hidden: 'translate-x-[calc(100%+1rem)]',
    handle: '-right-4 top-1/2 -translate-y-1/2',
    orientation: 'vertical',
    popupSide: 'left',
    popupAlign: 'center',
    tooltipSide: 'left',
  },
  'bottom-left': {
    root: 'bottom-4 left-4',
    hidden: 'translate-y-[calc(100%+1rem)]',
    handle: '-bottom-4 -left-4',
    orientation: 'horizontal',
    popupSide: 'top',
    popupAlign: 'start',
    tooltipSide: 'top',
  },
  bottom: {
    root: 'bottom-4 left-1/2 -translate-x-1/2',
    hidden: 'translate-y-[calc(100%+1rem)]',
    handle: '-bottom-4 left-1/2 -translate-x-1/2',
    orientation: 'horizontal',
    popupSide: 'top',
    popupAlign: 'center',
    tooltipSide: 'top',
  },
  'bottom-right': {
    root: 'bottom-4 right-4',
    hidden: 'translate-y-[calc(100%+1rem)]',
    handle: '-bottom-4 -right-4',
    orientation: 'horizontal',
    popupSide: 'top',
    popupAlign: 'end',
    tooltipSide: 'top',
  },
}

export const TOOLBAR_CLASSES =
  'relative z-50 inline-flex items-center gap-1 rounded-full border border-border bg-card p-1 text-foreground shadow-ui-lg motion-safe:transition-transform motion-safe:duration-300 motion-safe:ease-ui-out motion-reduce:transition-none max-sm:gap-0.5'

export const TOOL_BUTTON_CLASSES =
  'relative inline-flex size-11 shrink-0 items-center justify-center rounded-full text-foreground-secondary outline-none transition-colors hover:bg-muted hover:text-foreground ' +
  'focus-visible:ui-focus data-[active=true]:bg-primary data-[active=true]:text-primary-foreground ' +
  'max-sm:size-10 max-sm:after:absolute max-sm:after:-inset-0.5 max-sm:after:content-[\'\']'

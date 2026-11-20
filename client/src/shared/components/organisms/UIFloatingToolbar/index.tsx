import { Toolbar } from '@base-ui/react/toolbar'
import { cn } from 'cn'
import { useCallback, useEffect, useId, useRef, useState } from 'react'

import { UIBox } from '../../atoms/UIBox'
import { UIButton } from '../../atoms/UIButton'
import { UIIcon } from '../../atoms/UIIcon'
import { Popover, PopoverContent } from '../../shadcn/popover'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../shadcn/tooltip'

import { FloatingToolbarHandle } from './Handle'
import { HIDE_DELAY_MS, PLACEMENT_CLASSES, TOOL_BUTTON_CLASSES, TOOLBAR_CLASSES, TOOLTIP_DELAY_MS } from './constants'
import type { FloatingToolbarItem, UIFloatingToolbarProps } from './types'

export { FLOATING_TOOLBAR_PLACEMENTS, type FloatingToolbarItem, type FloatingToolbarPlacement, type UIFloatingToolbarProps } from './types'

/**
 * Barra flotante con navegación por teclado, una ventana no modal y asa accesible.
 *
 * @author Pablo Contreras
 * @since 2026/10/25
 */
export function UIFloatingToolbar({
  label,
  showLabel,
  closeLabel,
  items,
  placement,
  bottomNavOffset = false,
  autoHide,
  activeId,
  onActiveChange,
  children,
}: UIFloatingToolbarProps): React.JSX.Element {
  const [hidden, setHidden] = useState(false)
  const focusFirstAfterReveal = useRef(false)
  const [tooltipId, setTooltipId] = useState<string | null>(null)
  const id = useId()
  const rootRef = useRef<HTMLDivElement>(null)
  const toolbarRef = useRef<HTMLDivElement>(null)
  const popupRef = useRef<HTMLDivElement>(null)
  const titleRef = useRef<HTMLDivElement>(null)
  const activeTriggerRef = useRef<HTMLButtonElement>(null)
  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({})
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const tooltipTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const position = PLACEMENT_CLASSES[placement]
  const rootPosition = bottomNavOffset && placement.startsWith('bottom')
    ? position.root.replace('bottom-4', 'bottom-[calc(1rem+var(--ui-bottom-nav-offset))]')
    : position.root
  const activeItem = items.find((item) => item.id === activeId) ?? null
  const activeTriggerId = activeItem ? `${id}-trigger-${activeItem.id}` : null
  const titleId = `${id}-title`
  const isHidden = hidden && autoHide && activeId === null

  const cancelAutoHide = useCallback(() => {
    if (hideTimer.current !== null) {
      clearTimeout(hideTimer.current)
      hideTimer.current = null
    }
  }, [])

  const scheduleAutoHide = useCallback(() => {
    cancelAutoHide()
    if (!autoHide || activeId !== null) return
    hideTimer.current = setTimeout(() => {
      hideTimer.current = null
      setHidden(true)
    }, HIDE_DELAY_MS)
  }, [activeId, autoHide, cancelAutoHide])

  const cancelTooltip = useCallback(() => {
    if (tooltipTimer.current !== null) {
      clearTimeout(tooltipTimer.current)
      tooltipTimer.current = null
    }
    setTooltipId(null)
  }, [])

  const scheduleTooltip = useCallback((itemId: string) => {
    cancelTooltip()
    if (activeId === itemId) return
    tooltipTimer.current = setTimeout(() => {
      tooltipTimer.current = null
      setTooltipId(itemId)
    }, TOOLTIP_DELAY_MS)
  }, [activeId, cancelTooltip])

  const reveal = useCallback((focusFirst = false) => {
    cancelAutoHide()
    setHidden(false)
    if (focusFirst) focusFirstAfterReveal.current = true
  }, [cancelAutoHide])

  useEffect(() => {
    if (autoHide && activeId === null) {
      scheduleAutoHide()
    } else {
      cancelAutoHide()
    }

    return cancelAutoHide
  }, [activeId, autoHide, cancelAutoHide, scheduleAutoHide])

  useEffect(() => {
    if (!isHidden && focusFirstAfterReveal.current) {
      buttonRefs.current[items[0]?.id]?.focus()
      focusFirstAfterReveal.current = false
    }
  }, [isHidden, items])

  useEffect(() => () => {
    cancelAutoHide()
    if (tooltipTimer.current !== null) clearTimeout(tooltipTimer.current)
  }, [cancelAutoHide])

  function handleBlur(event: React.FocusEvent<HTMLDivElement>): void {
    const target = event.relatedTarget
    if (target instanceof Node && (rootRef.current?.contains(target) || popupRef.current?.contains(target))) return
    scheduleAutoHide()
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>): void {
    if (event.key === 'Escape' && activeId === null && autoHide) {
      cancelAutoHide()
      setHidden(true)
    }
  }

  function handleToolClick(item: FloatingToolbarItem): void {
    const nextActiveId = activeId === item.id ? null : item.id
    cancelTooltip()
    if (nextActiveId !== null) {
      activeTriggerRef.current = buttonRefs.current[item.id] ?? null
    }
    reveal()
    onActiveChange(nextActiveId)
  }

  return (
    <UIBox ref={rootRef} className={cn('fixed z-50 w-fit', rootPosition)}>
      <TooltipProvider delay={200}>
        <Toolbar.Root
          ref={toolbarRef}
          aria-label={label}
          orientation={position.orientation}
          inert={isHidden || undefined}
          className={cn(
            TOOLBAR_CLASSES,
            position.orientation === 'vertical' && 'flex-col',
            isHidden && position.hidden,
            activeItem !== null && 'max-sm:border-transparent max-sm:bg-transparent max-sm:shadow-none',
          )}
          onPointerEnter={cancelAutoHide}
          onPointerLeave={scheduleAutoHide}
          onFocus={cancelAutoHide}
          onBlur={handleBlur}
          onKeyDownCapture={handleKeyDown}
        >
          {items.map((item) => {
            const isActive = activeId === item.id
            const triggerId = `${id}-trigger-${item.id}`
            const trigger = (
              <Toolbar.Button
                ref={(element) => {
                  buttonRefs.current[item.id] = element
                  if (activeId === item.id) activeTriggerRef.current = element
                }}
                id={triggerId}
                type="button"
                aria-label={item.notice ? `${item.label}, ${item.notice}` : item.label}
                aria-haspopup="dialog"
                aria-expanded={isActive}
                data-active={isActive}
                className={TOOL_BUTTON_CLASSES}
                onPointerEnter={() => scheduleTooltip(item.id)}
                onPointerLeave={cancelTooltip}
                onFocus={() => scheduleTooltip(item.id)}
                onBlur={cancelTooltip}
                onClick={() => handleToolClick(item)}
              >
                <UIIcon name={item.icon} />
                {item.notice ? (
                  <UIBox as="span"
                    data-notice-dot
                    aria-hidden="true"
                    className="absolute top-1.5 right-1.5 size-2 rounded-full bg-destructive ring-2 ring-card"
                  />
                ) : null}
              </Toolbar.Button>
            )

            return (
              <UIBox as="span" key={item.id} className="contents">
                {item.separatorBefore ? (
                  <Toolbar.Separator
                    orientation={position.orientation === 'vertical' ? 'horizontal' : 'vertical'}
                    className={cn(
                      'shrink-0 bg-border',
                      position.orientation === 'vertical' ? 'h-px w-6' : 'h-6 w-px',
                    )}
                  />
                ) : null}
                <Tooltip
                  open={tooltipId === item.id && !isActive}
                  triggerId={triggerId}
                  onOpenChange={(open) => {
                    if (!open) cancelTooltip()
                  }}
                >
                  <TooltipTrigger id={triggerId} delay={200} render={trigger} />
                  <TooltipContent
                    role="tooltip"
                    side={position.tooltipSide}
                    align={position.popupAlign}
                    hidden={isActive}
                  >
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              </UIBox>
            )
          })}
        </Toolbar.Root>

        {isHidden ? (
          <FloatingToolbarHandle label={showLabel} className={position.handle} vertical={position.orientation === 'vertical'} onReveal={reveal} />
        ) : null}

        <Popover
          open={activeItem !== null}
          triggerId={activeTriggerId}
          onOpenChange={(open, details) => {
            if (!open && details.reason === 'outside-press') return
            if (!open) {
              cancelTooltip()
              reveal()
              onActiveChange(null)
            }
          }}
        >
          {activeItem ? (
            <PopoverContent
              ref={popupRef}
              anchor={toolbarRef}
              side={position.popupSide}
              align={position.popupAlign}
              sideOffset={8}
              initialFocus={titleRef}
              finalFocus={activeTriggerRef}
              role="dialog"
              aria-labelledby={titleId}
              className={cn(
                // En móvil, el anillo del color de fondo tapa la tarjeta de la página que queda detrás del panel.
                'flex min-w-0 w-[min(40rem,calc(100vw-2rem))] max-h-[min(30rem,calc(100dvh-8rem))] flex-col overflow-hidden rounded-2xl border border-border bg-card p-4 text-foreground shadow-ui-lg max-sm:shadow-none max-sm:ring-8 max-sm:ring-background sm:p-6 motion-safe:animate-ui-pop',
                position.orientation === 'vertical' && 'max-sm:max-w-[calc(100vw-5rem)]',
              )}
            >
              <UIBox className="mb-4 flex shrink-0 items-start justify-between gap-4">
                <UIBox role="heading" aria-level={2} ref={titleRef} id={titleId} tabIndex={-1} className="ui-typography-subtitle">
                  {activeItem.label}
                </UIBox>
                <UIButton
                  variant="ghost"
                  icon="x"
                  className="min-h-11 min-w-11 p-0"
                  aria-label={closeLabel(activeItem.label)}
                  onClick={() => {
                    cancelTooltip()
                    reveal()
                    onActiveChange(null)
                  }}
                >
                  {closeLabel(activeItem.label)}
                </UIButton>
              </UIBox>
              <UIBox className="-m-1 min-h-0 overflow-y-auto p-1">{children}</UIBox>
            </PopoverContent>
          ) : null}
        </Popover>
      </TooltipProvider>
    </UIBox>
  )
}

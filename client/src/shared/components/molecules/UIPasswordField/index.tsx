import { type ComponentProps, type KeyboardEvent, useId, useState } from 'react'

import { Button } from '../../shadcn/button'

import { UIField } from '../UIField'
import { UIBox } from '../../atoms/UIBox'
import { UIIcon } from '../../atoms/UIIcon'

type Props = Omit<ComponentProps<'input'>, 'type'> & {
  label: string
  error?: string
  revealLabel: string
  capsLockLabel: string
  hideLabel?: boolean
}

/**
 * Campo de contraseña: botón para mostrarla (`aria-pressed`) y aviso de
 * Bloq Mayús en una región viva. Al mostrarse desactiva corrector y
 * autocapitalización para no filtrar la clave.
 *
 * @author Pablo Contreras
 * @since 2026/09/27
 * @since 2026/11/19
 */
export function UIPasswordField({ label, error, revealLabel, capsLockLabel, hideLabel, id, onKeyDown, onKeyUp, ...props }: Props): React.JSX.Element {
  const generated = useId()
  const inputId = id ?? generated
  const [visible, setVisible] = useState(false)
  const [capsLock, setCapsLock] = useState(false)
  const track = (event: KeyboardEvent<HTMLInputElement>): void => setCapsLock(event.getModifierState('CapsLock'))

  return (
    <UIField
      {...props}
      id={inputId}
      label={label}
      hideLabel={hideLabel}
      error={error}
      type={visible ? 'text' : 'password'}
      icon="lock"
      autoCapitalize="off"
      autoCorrect="off"
      spellCheck={false}
      onKeyDown={(event) => {
        track(event)
        onKeyDown?.(event)
      }}
      onKeyUp={(event) => {
        track(event)
        onKeyUp?.(event)
      }}
      endSlot={
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={revealLabel}
          aria-pressed={visible}
          aria-controls={inputId}
          onClick={() => setVisible((current) => !current)}
          className="size-11 rounded-lg text-muted-foreground transition-colors duration-200 hover:text-foreground focus-visible:ui-focus motion-reduce:transition-none"
        >
          <UIIcon key={visible ? 'hide' : 'show'} name={visible ? 'eye-off' : 'eye'} className="size-5 motion-safe:animate-ui-fade" />
        </Button>
      }
      hint={
        <UIBox role="status" className="flex items-center gap-1.5 font-bold text-foreground-secondary">
          {capsLock ? (
            <>
              <UIIcon name="arrow-big-up" className="size-4" />
              {capsLockLabel}
            </>
          ) : null}
        </UIBox>
      }
    />
  )
}

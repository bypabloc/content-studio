import { useEffect, useRef } from 'react'

import { UIAlert } from '../UIAlert'
import { UIText } from '../../atoms/UIText'
import { UIBox } from '../../atoms/UIBox'
import { UILink } from '../../atoms/UILink'

type Props = { title: string; errors: { id: string; message: string }[] }

/**
 * Resumen de errores al enviar: un enlace por cada campo con error, anclado a
 * su `id`. Sin errores no pinta nada. Al aparecer toma el foco para que el
 * lector de pantalla anuncie los errores antes que los campos. Usa `UIAlert`
 * con tono de peligro.
 *
 * @author Pablo Contreras
 * @since 2026/11/10
 * @since 2026/11/19
 */
export function UIErrorSummary({ title, errors }: Props): React.JSX.Element | null {
  const ref = useRef<HTMLDivElement>(null)
  const hasErrors = errors.length > 0

  useEffect(() => {
    if (hasErrors) ref.current?.focus()
  }, [hasErrors])

  if (!hasErrors) return null

  return (
    <UIAlert tone="danger" ref={ref} tabIndex={-1} className="focus:ui-focus">
      <UIText variant="heading">{title}</UIText>
      <UIBox role="list" className="list-disc pl-5">
        {errors.map((error) => (
          <UIBox role="listitem" key={error.id} className="list-item">
            <UILink href={`#${error.id}`} className="underline">
              {error.message}
            </UILink>
          </UIBox>
        ))}
      </UIBox>
    </UIAlert>
  )
}

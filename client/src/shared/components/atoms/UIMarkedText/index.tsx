/** Un trozo de texto: sin `message` va normal; con `message`, es un aviso y se subraya con él en su `title`. */
export type MarkedSegment = { text: string; message?: string }

const SPACE = ' '

/**
 * Texto en línea con trozos subrayados: lo que va detrás de un campo para marcar sus avisos. Es un átomo porque necesita
 * `span` y `mark` con su estilo exacto (un contenedor `flex` cortaría el texto en renglones). Va en `aria-hidden`: quien
 * lee es el campo. `trailingSpace` deja alto el último renglón si el texto acaba en salto de línea.
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIMarkedText({
  segments,
  className,
  trailingSpace = false,
}: {
  segments: readonly MarkedSegment[]
  className: string
  trailingSpace?: boolean
}): React.JSX.Element {
  return (
    <div aria-hidden="true" className={className}>
      {segments.map((segment, index) =>
        segment.message === undefined ? (
          <span key={index}>{segment.text}</span>
        ) : (
          <mark
            key={index}
            title={segment.message}
            className="bg-transparent text-transparent underline decoration-destructive decoration-wavy underline-offset-4"
          >
            {segment.text}
          </mark>
        ),
      )}
      {trailingSpace ? SPACE : null}
    </div>
  )
}

/**
 * Una diferencia de palabras de una toma: la etiqueta, lo que se esperaba tachado (`del`) y lo que whisper oyó insertado
 * (`ins`). Es un átomo porque usa esas dos etiquetas (spec 008, D-4).
 *
 * @author Pablo Contreras
 * @since 2026/11/19
 */
export function UIDiffText({ label, expected, said }: { label: string; expected: string; said: string }): React.JSX.Element {
  return (
    <>
      {label} <del>{expected}</del> <ins>{said}</ins>
    </>
  )
}

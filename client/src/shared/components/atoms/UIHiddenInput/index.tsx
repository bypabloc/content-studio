/**
 * Campo oculto que lleva un valor al formulario sin mostrarlo. Lo usan los selectores que no
 * tienen un input propio, como el buscador de diagnósticos, que envía el id del código elegido.
 *
 * @param props.name - Nombre del campo en los datos del formulario.
 * @param props.value - Valor que se envía; vacío si todavía no hay selección.
 * @returns Un `input` oculto.
 *
 * @author Pablo Contreras
 * @since 2026/10/22
 */
export function UIHiddenInput({ name, value }: { name: string; value: string }): React.JSX.Element {
  return <input type="hidden" name={name} value={value} />
}

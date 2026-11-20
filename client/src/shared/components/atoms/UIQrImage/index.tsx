type Props = {
  src: string
  alt: string
}

/**
 * Código QR de la app de autenticación: la imagen PNG en `data:` que entrega el server, con tamaño fijo.
 * El texto alternativo lo pone quien lo muestra, porque describe para qué sirve el código.
 *
 * @author Pablo Contreras
 * @since 2026/10/31
 */
export function UIQrImage({ src, alt }: Props): React.JSX.Element {
  return <img src={src} alt={alt} className="size-48 rounded-xl" />
}

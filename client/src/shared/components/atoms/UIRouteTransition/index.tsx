/**
 * Entrada animada del contenido de cada ruta: envuelve la página con
 * `motion-safe:animate-ui-enter` (solo si el usuario permite movimiento) sin
 * cambiar el flujo del contenedor donde se monta; el shell no se anima.
 *
 * @author Pablo Contreras
 * @since 2026/10/13
 */
export function UIRouteTransition({ children }: { children: React.ReactNode }): React.JSX.Element {
  return <div className="motion-safe:animate-ui-enter">{children}</div>
}

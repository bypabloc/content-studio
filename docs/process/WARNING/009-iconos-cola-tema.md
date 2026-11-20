# 009: iconos de la cola, el tema y la paleta

- **Contexto**: D-2 y D-5 piden iconos en la cola, el tema y la paleta, pero no fijan tres detalles: el icono del pliegue de la cola (el mapa solo tiene `chevron-down`), el icono de un trabajo cancelado (D-2 reserva `cancel` para la acción) y cómo llega el `ref` de dnd-kit al asa cuando pasa por `UIIconButton`.
- **Elegida**:
  - `chevron-up` se suma al mapa de `UIIcon`, fuera de D-2: «Ocultar cola» usa `chevron-down` y «Mostrar cola», `chevron-up`. Es un icono genérico; `aria-expanded` sigue en el botón.
  - Iconos de estado: en cola `clock`; corriendo `loader-circle` con giro (`animate-spin motion-reduce:animate-none`, como el cargador de `UIButton`); listo `circle-check`; error `circle-alert`; cancelado `ban`, que no se confunde con la acción `cancel`.
  - `UIThemeToggle` sin `visibleLabel` es un `UIIconButton` (D-4): el tooltip de `UITooltip` reemplaza el atributo `title`. Su contrato baja a `labels: { toggle }`, porque `ThemeLabels` solo lo usaba él; `Shell` arma el nombre con `theme.change`, que dice el modo actual y el siguiente.
  - El asa de arrastre es un `UIIconButton`. El `ref` (`setActivatorNodeRef`) llega por props, porque React 19 trata `ref` como prop: no hace falta `forwardRef`.
  - La paleta pone el icono de cada sección antes del texto (`CommandItem.icon`, opcional).
- **Descartadas**:
  - `chevrons-up-down` para los dos estados: el cambio de estado se leería solo por la etiqueta.
  - Dejar `title` en el tema: no se muestra con el teclado y no cumple AC-4.
  - `circle-x` para cancelado: es el icono de la acción Cancelar.
  - `forwardRef` en `UIIconButton`: React 19 ya pasa el `ref`.
- **Cómo revertir**: el commit `feat: tema, nav, cola y paleta con iconos` deja cada cambio en su archivo; revertirlo devuelve las claves `queue.*` y los iconos de tema `sun`, `moon` y `monitor`.
- **Cómo comprobarla**: `bunx vitest run` en `client/` (`QueuePanel`, `UIThemeToggle`, `UICommandPalette` y `navItems`) y `python -m devtools test-runner --type=all`.
- **Pendiente**: la mirada visual de la cola y del tema en la app real va con [PENDING/008-revision-visual-organismos](../PENDING/008-revision-visual-organismos.md).

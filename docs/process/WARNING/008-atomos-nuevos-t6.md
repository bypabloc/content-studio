# 008: átomos nuevos y `role` en vez de etiquetas nativas en la migración de `features/` y `app/`

- **Contexto**: T6 quita las etiquetas nativas que quedaban fuera de átomos: `output` en `UICombobox` y `UIPasswordField`, `img` en `UIRemoteImage`, `aside` en la narración, y `div`, `button` y `span` en `Player`. `UIBox` no puede ganar `output` ni `UIStack` un `as`: D-4 cierra la lista de etiquetas (`008-ui-box`).
- **Elegida**:
  - `output` → `UIBox role="status"` (es el rol implícito del elemento). `aside` → `UIStack role="complementary"` en la columna de opciones (el mismo landmark).
  - `img` → átomo nuevo `atoms/UIImage`, con `alt` obligatorio en el tipo y su test espejo. `UIRemoteImage` lo usa.
  - `UIIcon` gana `play` y `pause` (Lucide), para que el reproductor no pinte glifos de texto.
  - `Player`: fila con `UIStack`, botón `UIButton` de 44 px (`size-11`, el área táctil de `UIButton`) y la onda en un `UIStack` con `ref`. El espacio entre botón y onda pasa de 12 px a 8 px (`gap="sm"`; la escala no tiene 12 px).
  - `App` usa `UIPage` (contenedor de pantalla), `UIText` y `UIButton`.
  - Clave nueva `ui.dialog.close` en los tres catálogos.
- **Descartadas**:
  - Añadir `output` a `UIBox`: amplía la lista cerrada de D-4.
  - Añadir `as` a `UIStack`: el mismo motivo para `aside`, y el `role` basta.
  - Mantener los glifos ▶ y ❚❚ en un `span`: no son íconos del sistema, y un `span` fuera de átomos rompe AC-2.
  - Conservar el botón de 36 px: queda por debajo del área táctil de 44 px.
- **Cómo revertir**: cada cambio es local a su archivo. Si `UIRemoteImage` vuelve a `img`, `ui-structure` tiene que admitirlo.
- **Cómo comprobarla**: `bun run --cwd client test -- atoms/UIImage features/narration shared/media` y, en T7, `python -m devtools test-runner --type=ui-structure --git-mode=all` con 0 hallazgos. El aspecto de estos cambios se mira en `008-revision-visual-organismos`.
- **Antes de**: el merge a `dev`.

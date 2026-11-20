# 008: `LicenseDialog` vive en `features/narration` y usa `UIDialog`

- **Contexto**: `LicenseDialog` estaba en la raíz de `shared/components/` sin nivel de D-3 (la ficha PENDING `008-licensedialog-ubicacion`, que esta spec cierra). Solo lo usa `NarrationOptions`, y su motor y su texto son de la narración.
- **Elegida**: moverlo a `features/narration/LicenseDialog.tsx` con `git mv` (y su test espejo) y reescribirlo sobre el organismo `UIDialog`: el texto va en `UIText` y los botones en el pie, con `UIButton`. El botón de cierre se nombra `ui.dialog.close` («Cerrar»), para que no compita con «Cancelar».
- **Descartadas**:
  - Dejarlo en `shared/components/` como molécula: no es un bloque de D-3 y lo usa una sola pantalla.
  - Un organismo genérico `UILicenseDialog`: pediría props que hoy nadie más usa (KISS).
  - Conservar su `div` y su `button`: rompen AC-2, que la etapa `ui-structure` hará cumplir.
- **Cambio de comportamiento**: al abrir, el foco ya no cae en «Aceptar» (el componente viejo lo fijaba con `focus()`). Así Enter no acepta una licencia sin leerla. Escape y el cierre siguen llamando a `onCancel`.
- **Cómo revertir**: `git revert` del commit de T6, o devolver el archivo a `shared/components/` con su marcado propio.
- **Cómo comprobarla**: `bun run --cwd client test -- features/narration/LicenseDialog` (nombre y aceptar o cancelar, licencia comercial, Escape, otras teclas y foco).
- **Antes de**: el merge a `dev`.

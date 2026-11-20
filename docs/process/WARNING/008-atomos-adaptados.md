# 008: los átomos de klinikae se adaptan en tres puntos: el enlace va con hash, el set de íconos se recorta, y los tests de texto no usan jest-dom

- **Contexto**: los 22 átomos llegan de klinikae. Tres cosas no encajan con content-studio: `UILink` usa `next/link` (el router aquí es por hash, D-3), `UIIcon` trae íconos de la clínica (`stethoscope`, `pill`, `flask-conical`, `glasses`, `crown`, `anchor`) y los tests usan `toBeInTheDocument`, que el setup no trae.
- **Elegida**:
  - `UILink` es una `<a>` que recibe `href` de hash (`#/narration`). `next` queda en `node_modules` por una dependencia de shadcn, pero no se importa.
  - `UIIcon` quita los íconos de la clínica y suma `panel-left-close`, `panel-left-open` y `list-ordered` (el shell y la cola). Los demás del set se quedan.
  - Las pruebas nuevas usan `classList`, `getAttribute` y `textContent`; no se agrega `@testing-library/jest-dom`.
  - `UIStack` suma `direction` (`column` por defecto), `align` y `justify`.
  - `UITooltip` pone `role="tooltip"` en el popup: sin él la tooltip no tiene nombre para los lectores de pantalla.
  - En `client/.oxlintrc.json`, `react/jsx-no-literals` se apaga para `tests/**`: el texto de prueba no es UI.
- **Descartadas**:
  - Mantener `next/link` con un alias: arrastra un router que content-studio no usa.
  - Agregar `jest-dom`: una dependencia nueva para cuatro aserciones.
- **Cómo revertir**: cada punto es independiente; `UILink` vuelve a `NextLink` con la dependencia y el set de íconos vuelve con sus entradas.
- **Cómo comprobarla**: `bun run --cwd client test -- components/atoms` (96 casos) y `python -m devtools test-runner --type=client-lint`.
- **Antes de**: el merge a `dev`.

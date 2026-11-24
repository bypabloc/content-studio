# 008: las moléculas no tienen etiquetas nativas; se sustituyen por átomos, o por roles ARIA cuando no hay átomo

- **Contexto**: D-4 y AC-2 prohíben `div`, `span`, `p`, `ul`, `li`, `table`, `input`, `label`, `a` y `svg` fuera de átomos y shadcn. Veinte de las 29 moléculas de klinikae las usan.
- **Elegida**:
  - `div` y `span` → `UIBox` (con `as="span"` en línea); `p` → `UIText`; `nav` → `UIBox as="nav"`.
  - `ul`, `ol`, `li` → `UIBox role="list"` y `role="listitem"`. Donde el contenedor usa `list-disc` (`UIErrorSummary`), el ítem lleva `list-item` para conservar las viñetas.
  - La tabla de `UIMonthGrid` → `role="grid"`; sus filas, `role="row"` con `display: contents`; celdas, `role="gridcell"`; encabezados, `role="columnheader"`.
  - `dl`, `dt` y `dd` de `UIDescriptionList` → `role="list"` y `role="listitem"`, con término y detalle como bloques `UIBox`.
  - `input` oculto → `UIHiddenInput`; `input` visible → `Input` de shadcn; `label` → `Label` de shadcn; `a` → `UILink` con `href` de hash.
  - `svg` de `UIQrCode`: el componente pasa a `atoms/UIQrCode`, porque envuelve un solo elemento nativo. D-3 permite mover un componente cuyo nivel real es otro, y se anota aquí.
  - `UIFieldFrame` (átomo nuevo, con test espejo): el marco de label, control, error y pista que se repetía en seis moléculas (ciclo 3, REFACTOR, con la condición de «tres o más»). La pista va tras el error en `Textarea` y `Combobox`; `FileField` la pone dentro del control porque su orden es control, pista y error.
- **Descartadas**:
  - Ampliar `UIBox` con `ul`, `dl` o `table`: la lista de `as` de D-4 queda cerrada, y ampliarla abre la regla.
  - Átomos `UIList` o `UITable`: no hay un caso que los pida; los roles bastan y se verifican en los tests.
- **Cómo revertir**: cada sustitución es local a su molécula. Volver a la etiqueta nativa exige quitar la regla de `ui-structure` (T7), no solo cambiar el archivo.
- **Cómo comprobarla**: `bun run --cwd client test -- components/atoms components/molecules` (las aserciones de `dl`, `table` y `ol` están en roles). En T7, `python -m devtools test-runner --type=ui-structure --git-mode=all` con 0 hallazgos.
- **Antes de**: el merge a `dev`.

# 008: gráficas con carga perezosa y dos átomos nuevos fuera del inventario de D-3

- **Contexto**: recharts y shadcn/chart pesan y solo hacen falta al dibujar una gráfica. D-4 prohíbe el `path` de la cruz y el `svg` del hueco dentro de un organismo. El hueco usaba el atributo `height` a propósito, sin prop `style`.
- **Elegida**:
  - `UIChart` se parte en `types.ts` (tipos), `axis.ts` (`axisWidth`, función pura sin recharts), `body.tsx` (recharts, con `UIChartBody`) e `index.tsx` (entrada con `lazy()` y `Suspense`). El `UIChart` público sigue exportando los mismos tipos y `axisWidth`.
  - Átomo `UIChartMarker` (el `path` de la cruz; sin coordenadas, un `g` vacío) y átomo `UIChartPlaceholder` (el `svg` con `height`, para reservar la altura sin `style`). Quedan fuera de los 64 de D-3; la tabla los suma en T8 (`docs/process/PENDING/008-inventario-d3.md`).
  - `UIChartCard` y el `Suspense` de `UIChart` muestran el mismo esqueleto, con la altura final.
  - Los tests de `UIChart` esperan a que dibuje (`findAllByRole('figure')` o `waitFor`) en vez de leer las props en síncrono, porque la carga es asíncrona.
- **Descartadas**:
  - Cargar recharts en el bundle inicial: la gráfica pesaría en la primera pantalla aunque no se vea.
  - `style={{ height }}` en el hueco: klinikae lo evita a propósito.
  - Una cruz con `path` dentro de `organisms/UIChart/body.tsx`: `ui-structure` (T7) la marcaría.
- **Cómo revertir**: volver a un solo `UIChart/index.tsx` con recharts directo, y quitar los dos átomos y sus tests.
- **Cómo comprobarla**: `bun run --cwd client test -- components/organisms/UIChart atoms/UIChartMarker atoms/UIChartPlaceholder`. La carga perezosa saca recharts del bundle inicial: se confirma con `python -m devtools test-runner --type=budget`.

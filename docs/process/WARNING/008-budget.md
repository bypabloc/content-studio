# 008: el bundle inicial crece 69,7 kB gzip y el límite pasa a 228 kB

- **Contexto**: D-9 permite que el bundle inicial crezca hasta 90 kB gzip sobre el baseline de la 007. Hay que medirlo y ajustar el límite de `client/budget.json`.
- **Medido** (kB gzip, 1 kB = 1024 bytes, con `measure()` de `devtools/test_runner/budget.py`):

  | Build | Inicial (`index-*.js`) | Diferido | Total |
  | :--- | :--- | :--- | :--- |
  | 007 (`origin/dev`, c2b0611) | 137,47 | — | 137,47 |
  | 008 (esta rama, medida con el gate final) | 207,13 | `Picker-*.js`: 16,73 | 223,86 |
  | Delta | +69,66 | +16,73 | +86,39 |

- **Elegida**: el límite pasa de 250 a 228 kB (`initialJsGzipKb`). Es el baseline de la 007 más los 90 kB de D-9: 137,47 + 90 = 227,47, redondeado hacia arriba. El 250 lo puso `c446b6e`, de la 005, como tope general; con él, el gate no vería un crecimiento que D-9 limita. El gate mide el total de los JS (inicial y diferido) contra ese límite: 223,86 ≤ 228.
- **Chunks diferidos**: solo `Picker` (`SearchSelectPicker`, con `lazy()` en `UISearchSelect` y `UISelect`). D-9 también nombraba `recharts`, `UIDateRangePicker` y `UIFloatingToolbar`; no aparecen en el build porque ninguna pantalla los usa todavía. Por eso el `lazy()` de `UIChart` no genera un chunk, y lo generará cuando una pantalla lo use.
- **Descartadas**: dejar el 250. Con ese límite, un crecimiento de 90 kB pasa el gate.
- **Cómo revertir**: poner 250 en `client/budget.json`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=budget`. El reporte queda en `tmp/budget/report.json`.
- **Antes de**: el merge a `dev`.

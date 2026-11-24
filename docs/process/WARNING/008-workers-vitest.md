# 008: vitest usa como máximo 6 workers (`client/vite.config.ts`)

- **Contexto**: la etapa `client-unit` fallaba con 23 workers (uno por núcleo lógico, en un equipo de 24) mientras la máquina tenía otras sesiones y apps cargadas (65 % de CPU durante el gate). Fallaban tests de `UISelect`, `UISearchSelect`, `UIRecommendedSelect`, `NarrationOptions` y `NarrationPage`: `findByRole('combobox')` no encontraba el `Picker` cargado con `lazy()` dentro de los 5 s de `asyncUtilTimeout` (`client/tests/unit/setup.ts`). Aislados, los mismos tests pasaban.
- **Elegida**: `maxWorkers: 6` en `client/vite.config.ts`. Con 6, `molecules` y `features` pasan completos (46 archivos, 241 casos); con 23, fallan entre 1 y 5 casos según la carga. La etapa `client-unit` pasa con cobertura por archivo.
- **Descartadas**:
  - Subir `testTimeout` a 15 s: probado, no arregla la espera del `Picker`, que es un `findByRole` de 5 s.
  - Subir `asyncUtilTimeout` por encima de 5 s: alarga cada fallo sin quitarlo.
  - Quitar los `lazy()` de los selectores: cambia la carga de klinikae (ver `008-moleculas-adaptadas`).
- **Cómo revertir**: quitar `maxWorkers` de `client/vite.config.ts`. Los tests vuelven a fallar en equipos cargados.
- **Cómo comprobarla**: `python -m devtools test-runner --type=client-unit` (exit 0) y `bun run --cwd client vitest run molecules features` (46 archivos, 241 casos).
- **Antes de**: el merge a `dev`.

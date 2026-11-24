# 008: la jerarquía se hace cumplir con overrides de oxlint, y el inventario lo guarda un test

- **Contexto**: D-4 fija la jerarquía y AC-1 pide un inventario completo. Quedaban pendientes la tabla de D-3 (que no listaba
  los átomos reales) y el test de inventario (`docs/process/PENDING/008-inventario-d3`, que esta spec cierra).
- **Elegida**:
  - Seis `overrides` de `no-restricted-imports` en `client/.oxlintrc.json`, con grupos que no se solapan: `excludeFiles`
    deja cada archivo en un solo grupo. Así no depende de cómo oxlint combina dos overrides que coinciden con un archivo.
  - `ui-components.md` reescrito con la tabla de D-4 y los criterios de nivel. `frontend-stack.md` y `devtools.md` se
    actualizan y `rules --sync` copia las tres a `.claude/`.
  - Inventario: `client/tests/unit/src/shared/components/inventory.test.ts` compara las carpetas de `atoms/`, `molecules/` y
    `organisms/` con la lista real (D-3 más lo que llegó después), y comprueba `index.tsx`, el export y el test espejo. La tabla
    de D-3 de la spec se actualiza con los átomos reales.
  - `UIToast` es la única excepción al export `UI<Nombre>`: su componente es `UIToaster` (el contenedor de los avisos). La API
    `toast` vive en el mismo archivo y el resto del código la usa así; no se renombra la carpeta.
  - Los avisos de la regla van en `help`: el texto de cada override va ahí, y `message` lleva el genérico de oxlint.
  - El test de jerarquía corre oxlint sobre fixtures con el `.oxlintrc.json` real. Su módulo
    `devtools/test_runner/client_lint_hierarchy.py` existe porque la auditoría del espejo de devtools exige un módulo por test.
- **Descartadas**:
  - `react/forbid-elements` y `eslint-plugin-boundaries`: no distinguen capas por carpeta sin dependencias nuevas (KISS).
  - Renombrar la carpeta `UIToast` a `UIToaster`: D-3 la lista así y el resto del código ya importa `toast` de ella.
- **Cómo revertir**: quitar los `overrides` de `client/.oxlintrc.json`, el test de inventario y el módulo de jerarquía; las reglas de
  `ui-components.md` quedan como texto.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_runner/test_client_lint_hierarchy.py -q` (quince casos),
  `bun run --cwd client vitest run inventory` (seis casos) y `bun run --cwd client lint`.
- **Antes de**: el merge a `dev`.

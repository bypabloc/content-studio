# 008: las primitivas de shadcn son código de proveedor: quedan fuera de tamaño, ortografía y auditoría del espejo

- **Contexto**: las 27 primitivas se copian de klinikae «tal cual» (D-1). Varias pasan de 300 líneas o de 300 columnas (`sidebar.tsx` tiene 741 líneas, `sheet.tsx` una línea de 1190 columnas), traen comentarios en español de klinikae y no tienen un test por archivo.
- **Elegida**: `client/src/shared/components/shadcn/**` queda excluido de tres revisiones, igual que los componentes de shadcn ya estaban fuera de la auditoría del espejo en klinikae:
  - `tests/validators/file-size.json` (`exclude`): el validador de tamaño no las mide.
  - `cspell.config.yaml` (`ignorePaths`): ni su ortografía ni sus comentarios.
  - `devtools/test_runner/client_mirror.py` (`EXEMPT`): no piden un test espejo por archivo. El smoke test (`client/tests/unit/src/shared/components/shadcn/smoke.test.tsx`) comprueba que las 27 se importan.
  - La cobertura por archivo (`client/vite.config.ts`) las excluye por la misma razón.
- **Descartadas**:
  - Partir `sidebar.tsx` y `chart.tsx` en varios archivos y reformatear las líneas largas: rompe la comparación con shadcn, y el próximo `shadcn add` vuelve a dejarlos como estaban.
  - Un baseline de tamaño con estas 18 entradas: el baseline solo puede bajar y aquí crecería.
  - Ignorar las primitivas en oxlint: el lint pasa sobre ellas (`client-lint`), así que no hace falta.
- **Cómo revertir**: quitar las cuatro exclusiones y partir los archivos que pasen de 300 líneas o de 300 columnas.
- **Cómo comprobarla**: `python -m devtools test-runner --type=validators` y `--type=spelling --git-mode=all` pasan, y `bun run --cwd client test -- smoke` importa las 27 primitivas.
- **Antes de**: el merge a `dev`. Es una decisión de la spec; no bloquea `main`.

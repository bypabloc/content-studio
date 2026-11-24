# 003: mypy con `ignore_errors` por módulo para los errores heredados

- **Contexto**: `test-runner --type=typecheck` tiene que pasar sobre `server/src` y `devtools`. Al entrar, mypy marcaba 79 errores en 27 archivos: índices sobre `Optional`, `argparse` y `typer` con tipos dinámicos, `termios` solo en Windows, variables reasignadas con tipos distintos.
- **Elegida**: `[[tool.mypy.overrides]]` con `ignore_errors = true` para 23 módulos heredados (lista en `pyproject.toml`). El resto del código se chequea con `check_untyped_defs`. Corregir los 79 errores cambia comportamiento de producto y no cabe en la 003.
- **Descartadas**: `ignore_errors` global (esconde el código nuevo); `# type: ignore` línea a línea (mismo resultado, más ruido en 27 archivos).
- **Cómo revertir**: quitar la sección de overrides y corregir los errores de cada módulo.
- **Cómo comprobarla**: `python -m devtools test-runner --type=typecheck` sale con 0 y dice `Success`. Un error de tipos en un módulo que no está en la lista falla la etapa (`devtools/tests/unit/test_runner/test_typecheck.py::test_ac6_type_error_fails_the_stage`).
- **Pendiente**: [PENDING/003-bajar-baselines.md](../PENDING/003-bajar-baselines.md). Cada módulo sale de la lista al corregir sus errores.

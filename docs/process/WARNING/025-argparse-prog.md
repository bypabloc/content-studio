# 025: el fixture de parsers fija el prog de argparse

- **Contexto**: Python 3.15 (`argparse._prog_name`) deriva el `prog` de `__main__.__spec__` y de `sys.orig_argv`. Bajo pytest, el `usage` de los parsers sale como `python.exe generar.py`; el fixture `parsers.json` (3.12) espera `generar.py`.
- **Elegida**: `generate.parsers()` fija `ap.prog = 'generar.py'` tras construir cada parser. El fixture no cambia y el comportamiento tampoco.
- **Descartadas**: regenerar el fixture con `python.exe generar.py` (depende del lanzador, no es un comportamiento del CLI); parchear `sys.orig_argv` (usa un detalle privado de la implementación).
- **Cómo revertir**: quitar la línea `ap.prog = 'generar.py'` de `server/tests/integration/fixtures/generate.py`; el test vuelve a fallar bajo pytest en 3.14 o más.
- **Cómo comprobarla**: `uv run pytest server/tests/integration/test_characterization.py`.
- **Pendiente**: el `usage` real de `studio` en 3.15 se revisa en la verificación final (`studio <comando> --help`, verify-before-claiming-done.md §1).

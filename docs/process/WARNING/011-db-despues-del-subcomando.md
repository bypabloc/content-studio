# 011: `--db` también después del subcomando (cierra PENDING 004)

- **Contexto**: `studio --db RUTA jobs list` funcionaba y `studio jobs list --db RUTA` salía con 2. La 011 tocó el parser de `studio` (`music samples`), que es el momento que la ficha de 004 fijaba.
- **Elegida**: un padre compartido `_db_flag()` con `default=argparse.SUPPRESS`, en `tts`, `regenerate`, `music` (y `samples`) y `jobs list|cancel|retry`. Con `SUPPRESS`, si no se pasa después, el valor de arriba (`paths.DB`) sigue valiendo.
- **Descartadas**: quitar `--db` del nivel superior (rompería `studio --db … jobs list`, que ya usan la app y la documentación). `narration voices` no lo recibe: sus flags son de la herramienta que corre.
- **Cómo revertir**: quitar `_db_flag()` de los `parents=` de `build_parser` en `cli/main.py` y la línea de `AGENTS.md`.
- **Cómo comprobarla**: `cli/test_main.py::test_db_is_accepted_after_the_subcommand` (las dos posiciones dan 0) y `uv run studio jobs list --db <ruta>`.

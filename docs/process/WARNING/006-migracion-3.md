# 006: la migración de las tomas es la 3 del código, no la 2 del plan

- **Contexto**: el plan numera la migración de `starred` y `group_key` como 2, pero la 2 ya es `owner_pid` (spec 004). Con `PRAGMA user_version`, la siguiente versión es la 3.
- **Elegida**: la migración 3 de `MIGRATIONS` con `starred INTEGER NOT NULL DEFAULT 0`, `group_key TEXT` y su índice `jobs_group_key`. Las pruebas de versión esperan 3.
- **Descartadas**: renumerar `owner_pid` (rompería las bases ya migradas con la 004); una tabla aparte para las tomas (duplicaría filas, y la lista de trabajos necesita el estado de cada toma).
- **Cómo revertir**: quitar la migración 3 solo antes del merge a `dev`; una base ya migrada a la versión 3 no baja de versión sin borrarla.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/db/test_schema.py`.

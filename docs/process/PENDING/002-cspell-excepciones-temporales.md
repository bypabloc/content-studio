# 002: exclusiones temporales de cspell que cada ciclo quita

- **Qué**: `cspell.config.yaml` en `ignorePaths` deja fuera de la revisión, por ahora, `server/src/content_studio/cli/**`, `music/**`, `narration/grabar/**`, `devtools/**`, `server/tests/**`, `tests/**`, `.agents/hooks/**`, `.claude/hooks/**`, `cli.py` y `cspell.config.yaml`. Además, `server/data/narration/voices/catalog.json` (catálogo de voces: nombres propios y textos en español que el diccionario no trae).
- **Por qué no se hizo**: cada carpeta se traduce en su ciclo (D-3, plan §1). `cli/` (salvo `commands/`) y `grabar/` se borran con las specs 004 y 007; mientras tanto solo se ajustan imports y flags.
- **Cuándo**: 
  - ciclo 5 saca `music/` y `cli/commands/`;
  - ciclo 6 saca `devtools/`, `.agents/hooks/`, `.claude/hooks/` y `tests/`;
  - la 004 saca `cli/` (salvo lo que queda) y la 007 saca `grabar/`;
  - el ciclo 8 deja solo las exclusiones de D-1 y D-3.
- **Quién**: agente de la 002 en cada ciclo; la 004 y la 007 cierran lo que les toca.
- **Qué la cierra**: `uv run python -m devtools spelling` con exit 0 y `{"issues": 0}`, y sin la lista de ignorePaths salvo D-1 y D-3.

Fuera de ignorePaths ya hoy, y pendientes para los ciclos 6 y 8, hay 86 casos en archivos que no son código: `.github/workflows/sync-dev.yml` (30), `.github/workflows/origen-pr.yml` (17), `.git-hooks/pre-push` (20), `.claude/mods/handoff-compact/` (16) y `server/pyproject.toml` (3). El pre-commit solo revisa lo staged, así que no bloquean los commits intermedios, pero sí la CI (`calidad.yml` corre spelling sobre todo lo versionado).

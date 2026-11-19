# 002: exclusiones temporales de cspell que cada ciclo quita

- **Qué**: `cspell.config.yaml` en `ignorePaths` deja fuera de la revisión, por ahora, `server/src/content_studio/cli/**` (salvo `commands/`), `narration/grabar/**`, `cli.py` y `cspell.config.yaml`. Además quedan dos excepciones de D-1: `server/data/narration/voices/catalog.json` (nombres propios y textos en español que el diccionario no trae) y `.agents/hooks/handoff_text.py` (prosa en español para el agente). Los datos de caracterización `server/tests/fixtures/*.json` y `*.txt` también quedan en español por D-1.
- **Por qué no se hizo**: cada carpeta se traduce en su ciclo (D-3, plan §1). `cli/` (salvo `commands/`) y `grabar/` se borran con las specs 004 y 007; mientras tanto solo se ajustan imports y flags.
- **Cuándo**:
  - ciclo 5 sacó `music/` y `cli/commands/` (commit `373f65b`);
  - ciclo 6 sacó `devtools/`, `tests/`, `server/tests/`, `.agents/hooks/` y `.claude/hooks/` (commit del ciclo 6);
  - ciclo 8 saca `.github/`, `.git-hooks/pre-push`, `.claude/mods/` y `server/pyproject.toml`;
  - la 004 saca `cli/` (salvo lo que queda) y la 007 saca `grabar/`;
  - al cerrar el ciclo 8 solo quedan las exclusiones de D-1 y D-3.
- **Quién**: agente de la 002 en cada ciclo; la 004 y la 007 cierran lo que les toca.
- **Qué la cierra**: `uv run python -m devtools spelling` con exit 0 y `{"issues": 0}` sobre todo lo versionado, y sin la lista de ignorePaths salvo D-1 y D-3.

Fuera de alcance hoy, para el ciclo 8: **84 casos** en archivos que no son código: `.github/workflows/sync-dev.yml` (30), `.github/workflows/origen-pr.yml` (16), `.git-hooks/pre-push` (19), `.claude/mods/handoff-compact/` (16) y `server/pyproject.toml` (3). El pre-commit solo revisa lo staged, así que no bloquean los commits intermedios, pero sí la CI (`calidad.yml` corre spelling sobre todo lo versionado): no empujar a `dev` hasta cerrar el ciclo 8.

# 002: exclusiones de cspell que quedan a propósito

- **Qué**: `cspell.config.yaml` en `ignorePaths` deja fuera solo lo que decide D-1 y D-3:
  - `cli/`: ya no está excluida. La 004 quitó esa exclusión (D-3) junto con `cli.py`, el menú y el asistente de la raíz. Queda solo `grabar/`, hasta la 008.
  - `narration/grabar/**`: el paquete de grabación en español. Lo traduce la 008 (D-3).
  - `server/data/narration/voices/catalog.json`: nombres propios y textos en español del catálogo (D-1).
  - `server/tests/fixtures/*.json` y `*.txt`: datos de caracterización en español (D-1).
  - `.claude/session-handoff.json`: prosa en español para el agente, configuración del plugin de handoff (D-1).
  - `cspell.config.yaml`: no se revisa a sí misma.
- **Por qué no se hizo**: son textos que el usuario lee en español, o carpetas que se traducen en specs posteriores.
- **Cuándo**: la 004 ya quitó la exclusión de `cli/`; la 008 quita la de `grabar/`. Las de D-1 se quedan.
- **Quién**: agente de la 004 y de la 008 para lo suyo; el resto no cambia.
- **Qué la cierra**: `uv run python -m devtools spelling` con `exit 0` sobre todo lo versionado, que ya se cumple con esta lista.

Estado al cierre del ciclo 8: los 68 casos que quedaban fuera de código (`.github/workflows/*`, `.git-hooks/pre-push`, `server/pyproject.toml`) ya están traducidos. `.claude/mods/handoff-compact/` lo borró dev con el plugin de handoff. No hay casos de spelling fuera de estas exclusiones.

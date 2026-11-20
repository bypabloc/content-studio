# 004: `--db` solo se acepta antes del subcomando

- **Qué**: `studio --db RUTA jobs list` funciona; `studio jobs list --db RUTA` sale con 2 (`unrecognized arguments`).
- **Por qué no se hizo**: el orden actual es explícito y no bloquea nada. Aceptarlo después del subcomando cambia los parsers de `narration`, `music` y `jobs`.
- **Cuándo**: al tocar el CLI en la 010 o la 011, o antes si el usuario lo pide.
- **Quién**: agente.
- **Qué la cierra**: que `uv run studio jobs list --db RUTA` salga con 0, con una prueba en `server/tests/unit/src/content_studio/cli/`.

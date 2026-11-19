# 002: nombres en disco que siguen en español (voces construidas)

- **Qué**: `narration/voices/<voz>/aprobacion.json` (estado de aprobación de cada voz construida) sigue con su nombre en español. El código lo lee en `voices/catalog.py` y lo escribe en `voices/build.py`. En `cspell.config.yaml` tiene `cspell:ignore` local.
- **Por qué no se hizo**: D-4 no lo incluye en `move-data`, y renombrarlo sin migración dejaría sin estado de aprobación todas las voces construidas. Son datos del usuario: la spec no cambia voces construidas sin una migración (plan, «Datos del usuario»).
- **Cuándo**: antes de publicar la 002 o en la 004, junto con el catálogo de mensajes. Requiere una entrada nueva en `MIGRATIONS` (paso 3) de `devtools/move_data.py` que renombre `aprobacion.json` dentro de cada voz y que el código lea ambos nombres durante una corrida.
- **Quién**: usuario (decide si el nombre cambia) y agente (la migración).
- **Qué la cierra**: `uv run pytest devtools/tests/test_move_data.py -q` con el caso nuevo, y que `catalog.py` deje de necesitar `cspell:ignore aprobacion`.

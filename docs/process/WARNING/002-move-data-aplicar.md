# 002: aplicar `move-data --apply` en el checkout principal (T9)

- **Qué**: el dry-run (solo lectura) sobre el checkout principal muestra lo que `move-data --apply` renombra. Son datos del usuario:
  - `voces/`→`voices/`: 15 voces construidas con 375 archivos (`.wav`, `.txt` y `aprobacion.json`, que no se renombra).
  - `voces/.fuentes/`: 20 audios de fuentes CC0 y de dominio público.
  - `voz/`→`reference/`: 25 grabaciones de referencia (`.wav` y `.txt`), y `voz/tomas/`→`reference/takes/` con 13 tomas.
  - `motores/`→`engines/`: 28,3 GiB de repos de motores (CosyVoice, IndexTTS) con sus venvs. `move-data` renombra la carpeta y reescribe las rutas de instalación de los venvs.
  - `docs/guiones/`→`docs/scripts/`: 13 archivos.
- **Por qué no se hizo**: cambia de lugar grabaciones, voces aprobadas y motores de varios GB del usuario. Eso es la categoría `user-data` del handoff, y la decisión es del usuario, aunque la spec (D-4, T9) lo contemple. Sin el apply, el código nuevo no encuentra las voces ni las referencias del principal: `narration tts --voice` y las referencias fallan hasta correrlo.
- **Cuándo**: después de fusionar la rama en `dev`, en el checkout principal (`git switch dev && git pull`), antes de correr `narration tts` o `music` con datos reales.
- **Quién**: el usuario confirma. El agente corre `python -m devtools move-data --apply`, verifica conteos y tamaños contra este dry-run, y hace las corridas con `gpu-turn run --job=002-english-cspell`.
- **Qué la cierra**: `python -m devtools move-data --apply` con `applied: true` y ninguna colisión; después, `uv run pytest -m local` en verde y una corrida corta de `narration tts` y de `music` con su medición (duración, LUFS, espectrograma).
- **Antes de aplicar**: revisar que no quede un lock viejo en `tmp/turno-gpu/` (el lock nuevo es `tmp/gpu-turn/lock.json`) y que ningún proceso tenga abiertos los archivos de `motores/`.

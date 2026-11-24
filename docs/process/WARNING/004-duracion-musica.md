# 004: la música sale en 12 s y no en 15 porque el motor recorta el silencio

- **Contexto**: AC-10 pide `studio music --duration 15` con duración 15 s ± 0,5 s. ACE-Step recorta el silencio al final (`server/src/content_studio/music/engines/acestep.py:72`). La pista sale en 11,7 s (corrida de la CLI) y 12,2 s (corrida por la API). El mismo comando da 12,0 s en `dev` (PENDING 001).
- **Elegida**: no cambiar el recorte en esta spec. Cambiar la salida de audio es decisión del usuario (PENDING 001); la 004 mide y lo reporta.
- **Descartadas**: quitar el recorte (cambia la salida de audio sin que lo decida el usuario); ajustar el criterio de AC-10 dentro de la spec (no lo pide la spec).
- **Cómo revertir**: no aplica; esta spec no cambia el recorte.
- **Cómo comprobarla**: `ffprobe -v error -show_entries format=duration -of csv=p=0 out/music/2026-11-19-3-lofi-chill/acestep-lofi-chill.wav` sale 12.21.
- **Pendiente**: [PENDING/001-duracion-de-audio.md](../PENDING/001-duracion-de-audio.md). El usuario decide si el destino es la duración pedida o si el recorte basta. Antes de `main`: esa decisión.

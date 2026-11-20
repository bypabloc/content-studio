# 010: la toma de un micrófono que no da 48 kHz se convierte a 48 kHz al subirla

- **Contexto**: D-2 pide que el server remuestree las tomas que no llegan a 48 kHz y lo anote en `check.json`. El client no garantiza los 48 kHz: el dispositivo y el WebView deciden la frecuencia real. La ficha PENDING `010-remuestreo-48-khz` lo dejó para la subida de tomas.
- **Elegida**: `POST .../takes/{style}` lee la frecuencia de la cabecera del WAV con `wave` (stdlib). Si no es 48 kHz, la convierte con ffmpeg (`aresample=resampler=soxr`) antes de guardarla, y el trabajo `voice.check` lleva `source_rate`. El chequeo añade la nota `resampled` y `measures.source_rate`. Si la cabecera no se lee, la toma se guarda como llegó, como antes.
- **Descartadas**: convertir en el trabajo de chequeo (el chequeo mediría un archivo que cambia, y la toma quedaría a otra frecuencia hasta el veredicto; el chequeo solo mide); convertir en el client (el WebView no garantiza 48 kHz y el `AudioContext` puede no respetar la frecuencia pedida).
- **Cómo revertir**: quitar la llamada a `profile_takes.to_48k` en `add_take`; el chequeo sin `--source-rate` sigue igual.
- **Cómo comprobarla**: `server/tests/unit/src/content_studio/narration/test_profile_takes.py` (44,1 kHz sale a 48 kHz; 48 kHz no se toca) y `api/routes/test_voices.py` (la toma guardada a 48 kHz y el trabajo con `source_rate`).
- **Pendiente**: ninguno. La anotación va en `notes` (`resampled`) y `measures.source_rate`, con el formato de notas del chequeo, no como un booleano `resampled` como decía la ficha PENDING.

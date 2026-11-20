# 010: remuestrear la toma a 48 kHz en el server si el micrófono no da 48 kHz

- **Qué**: si el micrófono no da 48 kHz, la toma sale a su frecuencia real. D-2 pide remuestrear en el server con `aresample=resampler=soxr` y anotarlo en `check.json`. El hook `useRecorder` ya entrega la frecuencia que dio el dispositivo (`sampleRate`).
- **Por qué no se hizo**: la ruta de subida de tomas (`POST takes`) todavía recibe el WAV crudo, sin la frecuencia. La subida la hace la pantalla Grabar, que es el ciclo 7.
- **Cuándo**: en el ciclo 7, con la subida de la pantalla Grabar.
- **Quién**: agente.
- **Qué la cierra**: una prueba en `test_voices_api` o `test_takes.py` con una toma de 44,1 kHz que sale a 48 kHz y deja `resampled: true` en `check.json`.

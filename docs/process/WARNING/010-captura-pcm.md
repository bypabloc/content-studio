# 010: captura PCM sin procesado para las tomas (AC-3)

- **Contexto**: AC-3 pide una toma a 48 kHz, mono y 24 bits, sin el procesado del navegador (cancelación de eco, supresión de ruido y control automático de ganancia), porque la referencia de voz tiene que ser fiel. Hay micrófonos que no dan 48 kHz.
- **Elegida**: `getUserMedia` con `deviceId`, `channelCount: 1`, `sampleRate: 48000` y los tres procesados en `false` (`client/src/features/recording/capture/useRecorder.ts`). Un `AudioWorklet` (`recorder-worklet.ts`) acumula los Float32 en el hilo de audio, y `encodeWav` (función pura) escribe 24 bits. Si el dispositivo no da 48 kHz, el server convierte la toma a 48 kHz al subirla, con el conversor soxr de ffmpeg (`common/ffmpeg.py`, commit `2ec6d8f`).
- **Descartadas**: `MediaRecorder` (entrega un contenedor comprimido, no PCM). Dejar activo el procesado del navegador (quita energía y altera la voz).
- **Cómo revertir**: volver a `MediaRecorder`. AC-3 deja de cumplirse.
- **Cómo comprobarla**: `client/tests/unit/src/features/recording/capture/useRecorder.test.ts` (las restricciones de `getUserMedia`) y `encodeWav.test.ts`. La toma con un micrófono real la grabó el usuario en la app y la confirmó.

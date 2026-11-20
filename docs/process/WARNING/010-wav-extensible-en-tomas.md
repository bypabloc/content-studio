# 010: ffmpeg escribe las tomas de 24 bits como WAV extensible, y las pruebas las leen con soundfile

- **Contexto**: ffmpeg escribe PCM de 24 bits con cabecera `WAVE_FORMAT_EXTENSIBLE` (0xFFFE). El módulo `wave` de la librería estándar no lo lee (`unknown format: 65534`).
- **Elegida**: el server lee la frecuencia de la toma que llega (PCM, de la captura del client) con `wave`. Las pruebas comprueban la toma convertida con `soundfile`, que lee el formato extensible. El código de producción no abre la salida con `wave`, así que `narration/` sigue importando solo stdlib en el nivel superior.
- **Descartadas**: convertir a 16 bits para que `wave` la lea, porque pierde la resolución de 24 bits que pide la guía (AC-3).
- **Cómo revertir**: no hay contrato que revertir; cambiar la lectura de las pruebas a otra librería no toca el server.
- **Cómo comprobarla**: `test_profile_takes.py::test_a_take_from_a_44100_microphone_is_resampled_to_48k_and_keeps_its_source_rate` (lee la salida con `soundfile`).
- **Pendiente**: ninguno.

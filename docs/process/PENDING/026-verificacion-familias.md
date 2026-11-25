# 026: caso de verificación para las familias transcription y vision

- **Qué**: que `engines verify` de faster-whisper y vision ejecute el paso `verify` de su receta (import de la librería) en lugar de devolver «Unsupported engine family».
- **Por qué no se hizo**: `verification.py` es de la spec de Motores; la 026 solo cambia recetas.
- **Cuándo**: antes de publicar, porque la pantalla de Motores muestra el error.
- **Quién**: agente.
- **Qué la cierra**: test de `verification.py` para esas familias y «Verificar» en verde para los dos motores.

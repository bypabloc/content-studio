# 006: evaluar con whisper solo el párrafo regenerado

- **Qué**: que la toma regenerada tenga la evaluación de su párrafo (OK o REVISAR) en vez de «Sin evaluar», sin reintentar los bloques ajenos.
- **Por qué no se hizo**: AC-3 exige que los demás bloques queden idénticos. `evaluate()` reintenta los bloques con error de toda la toma (ver [WARNING 006-regenerar-sin-evaluacion](../WARNING/006-regenerar-sin-evaluacion.md)).
- **Cuándo**: después de cerrar la 006, antes de elegir una toma por su evaluación.
- **Quién**: agente.
- **Qué la cierra**: que `evaluate()` acepte los índices a evaluar y reintente solo esos; que `build_command` de la regeneración pase `--evaluate` cuando la original se evaluó; y una prueba con motor falso de que los bloques ajenos conservan su hash.

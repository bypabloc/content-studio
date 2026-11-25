# 026: faster-whisper en Python 3.15 y av nueva cuando onnxruntime tenga rueda cp315

- **Qué**: subir faster-whisper a 3.15 y probar una av que acepte `metadata_errors` o un faster-whisper que ya no lo pase.
- **Por qué no se hizo**: onnxruntime (dependencia de faster-whisper) no tiene rueda cp315 para Windows; av 19 quitó el argumento que usa faster-whisper 1.2.1.
- **Cuándo**: después de publicar, o al salir una onnxruntime con `cp315-win_amd64`.
- **Quién**: agente.
- **Qué la cierra**: `uv pip compile` de faster-whisper con `--python-version 3.15` sin error, y una transcripción idéntica a la de la versión actual.

# 026: qwen-0.6b en Python 3.15 cuando onnxruntime tenga rueda cp315

- **Qué**: probar qwen-0.6b en 3.15 con torch 2.14.1+cu130 y subir la receta solo si instala y genera.
- **Por qué no se hizo**: qwen-tts 0.1.1 depende de onnxruntime, cuya última versión (1.32.0) no tiene rueda cp315 para Windows.
- **Cuándo**: después de publicar, o al salir una onnxruntime con `cp315-win_amd64`.
- **Quién**: agente.
- **Qué la cierra**: `uv pip compile` de qwen-tts con `--python-version 3.15` sin error, y una instalación y salida corta correctas.

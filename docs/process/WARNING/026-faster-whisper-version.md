# 026: faster-whisper queda en Python 3.14 y av 18.1.1 (onnxruntime sin rueda cp315 y av 19 sin metadata_errors)

- **Contexto**: faster-whisper 1.2.1 depende de `onnxruntime`, cuya última versión (1.32.0) solo tiene ruedas Windows hasta `cp314`, así que 3.15 no resuelve. faster-whisper 1.2.1 pasa `metadata_errors` a `av.open`, y la av 19.0.2 ya no lo acepta (error al transcribir).
- **Elegida**: Python 3.14 con faster-whisper 1.2.1, av 18.1.1 (la última con `metadata_errors` y rueda abi3, válida en 3.14), ctranslate2 4.9.1 y nvidia-cublas 12.4.5.8 y nvidia-cudnn 9.1.0.70. Verificado: la transcripción de la narración de prueba (`prueba del aspect 026.`) es idéntica a la de la combinación anterior (3.12 con av 13.1.0).
- **Descartadas**: av 19.0.2 (sin `metadata_errors`); 3.15 (onnxruntime).
- **Cómo revertir**: poner `"version": "3.12"` y `av==13.1.0` (receta anterior, que sí transcribe).
- **Cómo comprobarla**: `transcribe_main --input <wav> --model small --language es --out <json>` con el Python del venv de faster-whisper, y comparar con la transcripción de la combinación anterior.
- **Pendiente**: [026-reintentar-faster-whisper](../PENDING/026-reintentar-faster-whisper.md).

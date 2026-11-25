# 036: corrida real de Transcripción con hablantes

- **Qué**: falta la sección en la app: nombres en el texto, renombrar, cerrar y reabrir desde la sección. La transcripción con hablantes ya corre por la API sobre un clip de dos personas (WDER 0,0 %, ver `10-pruebas-en-gpu.md`).
- **Cómo cerrarlo**: `python -m devtools app-check run --scenario=transcription` y revisar con `image-reader` las capturas. Renombrar, cerrar y reabrir con la app.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente.

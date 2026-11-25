# 036: corrida real de Transcripción con hablantes

- **Qué**: `app-check --scenario=transcription` pasa en claro y oscuro, sin errores de consola (run `20261125-181852`), y `image-reader` no encuentra bloqueos. Falta lo que no mide el escenario: nombres en el texto, renombrar, cerrar y reabrir desde la sección. La transcripción con hablantes ya corre por la API sobre un clip de dos personas (WDER 0,0 %, `10-pruebas-en-gpu.md`).
- **Cómo cerrarlo**: en la app instalada, con un clip de dos personas: renombrar un hablante, cerrar la sección y reabrirla. Ver `PENDING/039-aviso-motor-en-app-check` para el aviso de motor en `app-check`.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente, con la app instalada.

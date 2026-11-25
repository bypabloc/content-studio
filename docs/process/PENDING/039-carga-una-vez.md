# 039: carga del modelo una sola vez (AC-1)

- **Qué**: el AC-1 pide que solo la primera vez se cargue el modelo, según los logs de los trabajos. Los logs de `logs/jobs/<id>.log` salen vacíos y el trabajo no anota cuándo carga el modelo ni cuándo lo reusa. Los cuatro trabajos (Hablantes, Transcripción, Subtítulos y Limpiador) sí dan los mismos turnos, con 0,5 s de tolerancia en las pausas.
- **Cómo cerrarlo**: que el trabajo deje en su log cuándo carga el modelo y cuándo reusa la caché de la diarización, y medirlo en dos corridas seguidas del mismo clip.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente.

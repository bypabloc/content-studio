# 038: corrida real de subtítulos con hablantes

- **Qué**: el proyecto de subtítulos desde la transcripción trae hablante en cada cue (13 cues, ninguno contradice la diarización, por la API). `app-check --scenario=smoke` pasa en claro y oscuro (run `20261125-182130`), con subtítulos y Limpiador sin errores. Falta ver la vista previa con etiqueta y color de cada hablante, el quemado y el Limpiador con hablantes sobre sus cortes, en la app instalada.
- **Cómo cerrarlo**: en la app instalada, con el clip de dos personas: vista previa y quemado de subtítulos, y el análisis del Limpiador con hablantes. Ver `PENDING/039-aviso-motor-en-app-check`.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente, con la app instalada.

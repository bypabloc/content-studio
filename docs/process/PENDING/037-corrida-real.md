# 037: corrida real de la sección Hablantes

- **Qué**: `app-check --scenario=speakers` pasa en claro y oscuro (run `20261125-181852`) y `image-reader` no encuentra bloqueos. Falta comprobar que la línea de tiempo muestre los turnos de un clip de dos personas, no solo que la sección cargue. La diarización da esos turnos: DER 10,5 % sin collar y 9,2 % con collar de 0,25 s (`10-pruebas-en-gpu.md`).
- **Cómo cerrarlo**: en la app instalada, con el clip de dos personas, mirar la línea de tiempo y comparar con los turnos de `referencia.json`. Ver `PENDING/039-aviso-motor-en-app-check`.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: el agente, con la app instalada.

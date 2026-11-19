# 004: los cambios de la CLI sobre trabajos que el server no corre no salen por SSE

- **Qué**: `studio jobs cancel` sobre un trabajo que corre otro proceso actualiza la base, pero el evento no llega a `/events` hasta que el server publica el cambio.
- **Por qué no se hizo**: el broker de eventos vive en el proceso del server (una cola por suscriptor). Publicar desde la CLI pediría un canal entre procesos.
- **Cuándo**: antes de la 005, porque el cliente depende de SSE para el progreso.
- **Quién**: agente.
- **Qué la cierra**: un `studio jobs cancel` con el server en marcha que aparezca en `/events` en menos de 1 s.

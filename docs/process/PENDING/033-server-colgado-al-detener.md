# 033: Un server dejó de escuchar tras POST /server/stop pero no terminó y retuvo api.lock

- **Qué**: en la corrida real de la 033, un server lanzado con `api up` (con `CREATE_BREAKAWAY_FROM_JOB`), con una carpeta de entrada que se quitó y un `media.convert` hecho, cerró su puerto al detenerlo pero siguió vivo y con `api.lock`: `serve` salía con 3 y `api up` vencía a los 30 s. Se terminó a mano.
- **Por qué no se hizo**: la misma secuencia en un server aislado (`tmp/spec-033/stop_probe2.py`) terminó en 0,2 s; no se reprodujo.
- **Cuándo**: antes de publicar en `main`.
- **Quién**: agente.
- **Qué la cierra**: reproducirlo (volcar los hilos con `faulthandler` al recibir la orden de apagado) y corregirlo, o diez ciclos de `api up` y `api down` con trabajos sin cuelgue.

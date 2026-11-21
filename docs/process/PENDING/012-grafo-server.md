# 012: reconstruir el índice de graphify del server

- **Qué**: ejecutar `uv tool run graphify update .` y confirmar que el índice de `server/src` se genera.
- **Por qué no se hizo**: el intento anterior falló con WinError 5 al leer la exclusión global de Git.
- **Cuándo**: cuando Git permita leer esa configuración o antes de iniciar una búsqueda nueva del server.
- **Quién**: agente.
- **Qué la cierra**: `graphify update` termina sin error y `graphify query` responde sobre el código del server.

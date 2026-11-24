# 005: cerrar la ventana mientras el server arranca puede esperar hasta 30 s

- **Qué**: `ServerState::connect` mantiene el lock del estado durante `wait_for_ready`, que espera hasta 30 s la línea `ready`. Si la ventana se cierra en ese rato, `stop()` (en `RunEvent::Exit`) espera el mismo lock y la app tarda en salir.
- **Por qué no se hizo**: el caso solo pasa con un arranque lento o colgado. El arreglo cambia el orden del lock (soltarlo antes de esperar) y hay que probarlo con el server real.
- **Cuándo**: después de la 005, o antes si la verificación real de T9 lo muestra.
- **Quién**: agente.
- **Qué la cierra**: cerrar la ventana durante el arranque sale en menos de un segundo, y el server (si llegó a nacer) no queda vivo.

# 017: el runner e2e no termina después de las pruebas

- **Qué**: cuatro pruebas del Editor pasan y la ejecución directa listó las 61 pruebas de la suite como aprobadas, pero Playwright no salió ni mostró el resumen final. `test-runner --type=e2e` también quedó abierto después de las capturas de smoke.
- **Por qué no se cerró**: tras tres corridas, los procesos Node de Playwright/Vite siguen activos y el puerto 4173 deja de escuchar; interrumpí los procesos de prueba que quedaron esperando.
- **Cuándo**: antes de la publicación final, cuando el runner termine por sí solo y entregue exit 0 y el conteo completo.
- **Quién**: agente.
- **Qué la cierra**: `python -m devtools test-runner --type=e2e` termina con exit 0 y reporte completo.
- **Impacto**: los cuatro flujos del Editor sí pasaron individualmente; queda sin confirmar el exit 0 agregado de las 61 pruebas.

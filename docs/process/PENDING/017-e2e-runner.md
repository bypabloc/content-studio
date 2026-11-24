# 017: el runner e2e no termina después de las pruebas

- **Qué**: cuatro pruebas del Editor pasan y la ejecución directa listó las 61 pruebas de la suite como aprobadas, pero Playwright no salió ni mostró el resumen final. `test-runner --type=e2e` también quedó abierto después de las capturas de smoke.
- **Por qué no se cerró**: tras tres corridas, los procesos Node de Playwright/Vite siguen activos y el puerto 4173 deja de escuchar; interrumpí los procesos de prueba que quedaron esperando.
- **Cuándo**: antes de la publicación final, cuando el runner termine por sí solo y entregue exit 0 y el conteo completo.
- **Quién**: agente.
- **Qué la cierra**: `python -m devtools test-runner --type=e2e` termina con exit 0 y reporte completo.
- **Impacto**: los cuatro flujos del Editor sí pasaron individualmente; queda sin confirmar el exit 0 agregado de las 61 pruebas.

## Repetición en 019

- Los cuatro escenarios nuevos de 019 imprimieron `PASS` en ejecuciones enfocadas con Chromium de la caché local.
- La corrida enfocada conjunta de los cuatro también imprimió `PASS`, pero no entregó exit ni resumen.
- El test-runner integral quedó activo unos nueve minutos, sin reporte ni archivos de resultados; se interrumpió.
- Node y Playwright quedaron sin actividad de CPU durante la espera; no se confirmó el resultado agregado.
- La ficha sigue abierta hasta que `python -m devtools test-runner --type=e2e` termine con exit 0 y reporte completo.

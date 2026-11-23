# 018: Playwright no cierra los escenarios visuales

- **Qué**: el runner completo quedó abierto más de ocho minutos sin resumen. La ejecución aislada de T7 tampoco terminó; Chromium sí inicia con la caché de la 017.
- **Por qué no se cerró**: tras cuatro intentos, el proceso no entregó exit ni resultado final. Dos fallas iniciales eran selectores ambiguos y ya se corrigieron; la corrida posterior siguió abierta.
- **Cuándo**: repetir durante T8 y antes de la verificación integral de 023.
- **Quién**: agente.
- **Qué la cierra**: `python -m devtools test-runner --type=e2e` termina con exit 0 y reporte completo, incluidos los cuatro escenarios del Editor.
- **Impacto**: los tres escenarios de T7 están agregados, pero aún no tienen verificación e2e concluyente.
- **Reintento T8**: `uv run python -m devtools test-runner --type=e2e` quedó abierto, sin salida, durante varios minutos; se interrumpió con Ctrl+C y no entregó reporte. Repetir en 023.

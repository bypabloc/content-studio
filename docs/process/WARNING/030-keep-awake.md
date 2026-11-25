# 030: una carpeta con keep_awake retiene el server, con una retención por carpeta

- **Contexto**: D-4 y AC-8. `IdleClock` (spec 028) ya trae `hold` y `release`.
- **Elegida**: cada carpeta con `keep_awake` y sin pausa retiene `inbox:<id>`. El sondeo la suelta al pausarla, al quitar `keep_awake` o al quitar la carpeta (en el sondeo siguiente). Lo que se soltó con el server apagado se toma en el primer sondeo al arrancar.
- **Descartadas**: un contador global (no dice qué carpeta retiene); meter las carpetas en `_busy` (mezclaría archivos sin trabajo con trabajos de la cola).
- **Cómo revertir**: quitar `_holds` de `inbox/scanner.py` y su llamada en `scan_once`.
- **Cómo comprobarla**: `uv run pytest server/tests/integration/test_inbox.py::test_ac8_keep_awake_holds_the_server_until_released`.

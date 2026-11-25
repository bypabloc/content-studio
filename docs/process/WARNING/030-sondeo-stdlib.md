# 030: sondeo con stdlib cada 2 s; un archivo es estable si no cambia entre dos sondeos

- **Contexto**: 01 D-2. Hay que saber cuándo una app terminó de escribir un archivo que soltó en la carpeta, sin una dependencia nueva.
- **Elegida**: `os.scandir` del primer nivel cada 2 s (`inbox/scanner.py`). Un archivo se toma cuando su tamaño y su fecha son iguales en dos sondeos seguidos; el par queda en `inbox_items`. Se ignoran `.part`, `.tmp`, los ocultos y `~$*`.
- **Descartadas**: `watchdog` (una dependencia nueva para un sondeo de 2 s); eventos del sistema (distintos en Windows, WSL y unidades de red); esperar un tiempo fijo (un archivo grande copiado despacio se tomaría a medias).
- **Cómo revertir**: quitar `server/src/content_studio/inbox/scanner.py` y las líneas del hilo en `cli/serve.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/inbox/test_scanner.py`.
- **Nota**: 02 §4.1 escribe `scan_once(conn, now)`. Se quitó `now`: la estabilidad compara el tamaño y la fecha guardados, no un reloj, y el parámetro quedaría sin uso.

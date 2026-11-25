# 028: `studio serve` ya no imprime el token y el token persiste

- **Contexto**: antes, `serve` generaba un token nuevo en cada arranque y lo imprimía en la línea `ready` si no lo recibía. La spec pide que el token persista (AC-4) y que nunca salga en logs ni en la salida (`--with-token` solo para Tauri).
- **Elegida**: `serve` toma el token de `api-token` (persistente) o el de `--token`, y la línea `ready` lleva solo `port`. `--port` por defecto es `api.port` (41830); `--port 0` elige uno libre (tests y `app-check`).
- **Descartadas**: imprimir el token en `ready` (rompe la regla de no imprimirlo); un token nuevo por arranque (obliga a reconfigurar las apps externas en cada arranque).
- **Cómo revertir**: volver a generar el token en `serve` y a imprimirlo si no llega por `--token`. Afecta a `test_serve.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/cli/test_serve.py`.

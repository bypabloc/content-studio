# 029: el cliente lanza el `studio` de la instalación, o `uv run` sobre el checkout

- **Contexto**: el fragmento necesita una ruta absoluta que el cliente pueda ejecutar sin el PATH de la terminal.
- **Elegida**: en la app instalada (`CONTENT_STUDIO_MODE=installed`), `studio.exe` junto al Python de la app, con `mcp`;
  en un checkout, `uv` (ruta absoluta si está en el PATH) con `run --project <raíz>/server studio mcp`. El proyecto de
  `uv` está en `server/`, no en la raíz.
- **Descartadas**: `python -m content_studio` (no es el comando del proyecto y no lleva el venv de `uv`).
- **Cómo revertir**: `launch_command()` en `config.py`.
- **Cómo comprobarla**: `uv run studio mcp config --client claude-code` muestra la ruta de `uv` y `--project` del checkout.

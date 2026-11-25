# 030: `studio_watch_folder` registra la carpeta por la API, no por la base

- **Contexto**: `studio mcp` corre aparte y habla con el server de la instalación; 029 (D-2) dice que cada herramienta es una llamada a la API.
- **Elegida**: `Bridge._sync` llama `POST /inbox/folders`, igual que las demás herramientas. La CLI (`studio inbox`) sí escribe la base directa, como `studio library`; el server ve el cambio en su sondeo siguiente.
- **Descartadas**: que el MCP escriba la base (saltaría la validación de la API y el token); que la CLI llame a la API (exigiría un server encendido para registrar una carpeta).
- **Cómo revertir**: quitar la rama `studio_watch_folder` de `mcp_server/bridge.py`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/mcp_server/test_bridge.py::test_ac10_watch_folder_registers_the_folder_through_the_api`.

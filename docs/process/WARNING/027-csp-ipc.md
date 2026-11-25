# 027: la CSP permite el IPC de Tauri (ipc: y http://ipc.localhost)

- **Contexto**: `app-check` en claro falla con 4 errores de consola: la CSP de `client/src-tauri/tauri.conf.json` (`connect-src 'self' http://127.0.0.1:*`) bloquea `plugin:event|listen` y `get_connection` por `http://ipc.localhost`. AC-4 exige cero errores de consola. La ficha PENDING 026-csp-app-check lo registró.
- **Elegida**: agregar `ipc:` y `http://ipc.localhost` a `connect-src`. Es el ejemplo oficial de la CSP de Tauri v2 y solo permite el canal IPC de la propia app; no abre otro origen.
- **Descartadas**: quitar la CSP (aflojaría la seguridad de la ventana); dejarlo pendiente (AC-4 no pasa).
- **Cómo revertir**: quitar `ipc: http://ipc.localhost` de `connect-src` en `client/src-tauri/tauri.conf.json`. Vuelven los 4 errores de consola.
- **Cómo comprobarla**: `python -m devtools app-check run` con cero errores de consola en `smoke` en claro y oscuro.

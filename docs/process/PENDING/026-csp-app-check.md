# 026: app-check en claro falla por la CSP de Tauri (y un 403 en las voces)

- **Qué**: el escenario `smoke` en claro de `python -m devtools app-check run --data=real` falla con 4 errores de consola. La CSP de `client/src-tauri/tauri.conf.json` (`connect-src 'self' http://127.0.0.1:*`) bloquea `http://ipc.localhost/plugin:event|listen` y `get_connection`. El escenario en oscuro pasa sin errores.
- **Por qué no es de 026**: `client/src-tauri` no cambió desde `origin/dev` (`git diff e400c36 HEAD -- client/src-tauri` vacío). No se reprodujo en `origin/dev`.
- **Otro hallazgo**: `GET /media/peaks` de las voces da 403 (`forbidden_path` de `paths_guard`). No hace fallar el escenario, pero la forma de onda de las voces no sale. Tampoco es de 026.
- **Quién decide**: el usuario, porque tocar la CSP es un cambio de seguridad de la app.
- **Qué la cierra**: `app-check run --data=real` en verde, y decidir si `ipc.localhost` entra en `connect-src` y si las voces pueden pedir su forma de onda.

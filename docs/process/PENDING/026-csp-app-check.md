# 026: app-check: las voces dan 403 en /media/peaks

- **Qué**: `GET /media/peaks` de las voces devuelve 403 (`forbidden_path` de `paths_guard`). No hace fallar el escenario, pero la forma de onda de las voces no sale.
- **Resuelto en la 027**: la CSP. El fallo de consola de `app-check` se cerró con `ipc: http://ipc.localhost` en `connect-src` (WARNING `027-csp-ipc`).
- **Quién decide**: agente, con la revisión de `paths_guard`.
- **Qué lo cierra**: que las voces pidan su forma de onda por una ruta permitida o el endpoint la sirva.

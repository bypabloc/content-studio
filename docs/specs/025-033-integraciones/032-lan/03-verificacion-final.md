# Spec 032: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `032-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-032/` o `tmp/spec-032/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

Una sola vez, con todos los commits de las fases hechos y antes del push (plan-format.md §4). Si algo falla, se corrige con commits `fix: …` y se repite solo lo rojo.

## 1. Batería

| # | Comando | Aplica si |
| :--- | :--- | :--- |
| 1 | `uv run ruff check && uv run ruff format --check` | siempre |
| 2 | `python -m devtools test-runner --type=all` | siempre |
| 3 | `python -m devtools test-runner --type=e2e` | toca el client |
| 4 | `python -m devtools test-runner --type=tauri-check` | toca `client/src-tauri/` |
| 5 | `python -m devtools app-check run` | toca la UI o el arranque de la app |
| 6 | `uv run pytest server/tests/unit/src/content_studio/api server/tests/unit/src/content_studio/jobs` | toca la API |
| 7 | Escaneo desde otro equipo: `curl -k https://<ip>:41831/engines` (404) y `curl -k https://<ip>:41830/health` (sin respuesta) | siempre |

## 2. Comprobaciones propias

1. Activar la red local en la app instalada, aceptar el UAC y ver la regla con `netsh advfirewall firewall show rule name="Content Studio LAN"` [AC-9].
2. Desde otro equipo o el celular: emparejar con `curl -k -X POST https://<ip>:41831/pair -d '{"pin":"…","name":"celular"}'`, subir un `.wav`, encolar `media.convert` con `upload:<id>`, descargar el MP3 [AC-3, AC-6, AC-7].
3. Desde otra PC con un cliente MCP HTTP (Claude Code con `--transport http` y el header): listar herramientas y narrar [AC-8].
4. Revocar el dispositivo en la app: la siguiente petición da 401 [AC-4].

## 3. Escucha

No aplica: la spec no cambia el audio generado.

## 4. Cierre, PR y merge

- [ ] Toda decisión con su ficha en `WARNING/` y todo pendiente en `PENDING/`: lo que quede solo en esta carpeta se pierde.
- [ ] Fichas de `docs/process/01-done/` actualizadas: `integrations.md` (red local) y `server.md` (segundo listener).
- [ ] Reglas y docs actualizadas: `AGENTS.md` (la LAN y su opt-in), `stack.md` §1 (`cryptography`) y `command-output.md` (dónde van las subidas); `python -m devtools rules --sync` y `python -m devtools agent-context`.
- [ ] Spec de lote: deja sus fases en `IMP` y su fila del README del lote en `DON`; la carpeta la borra la 033.
- [ ] `git fetch origin dev` y merge de `origin/dev` si avanzó; un solo push.
- [ ] `gh pr list --head feature/032-lan`; si no existe, `gh pr create --base dev` con problema, solución, cómo probar (comandos reales) y fichas WARNING/PENDING.
- [ ] `gh pr checks <n> --watch`; con todo verde, `gh pr merge <n> --merge`.
- [ ] Desde el principal: `git fetch origin dev` y `python -m devtools worktree close 032-lan`.

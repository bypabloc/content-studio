# Spec 028: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `028-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-028/` o `tmp/spec-028/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'chore/027-client-deps' || echo FALLA
netsh int ipv4 show excludedportrange protocol=tcp   # 41830 fuera de los rangos
```

## 2. Contexto

Hoy la ventana de Tauri lanza `studio serve --port 0 --token <t>`, lee el puerto de la línea `ready` y mete el proceso en un Job de Windows que lo mata al cerrarse. Ninguna otra app puede encontrar ese server ni su token, y desaparece con la ventana. El CLI `studio` encola sin server, pero no sirve para clientes que hablan HTTP ni para el MCP (029).

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Server compartido | El único `studio serve` de una instalación, que usan la ventana, el MCP y los scripts | `runtime/instance.py` |
| Descubrimiento | `api.json` con URL, puerto, pid y versión | `runtime/discovery.py` |
| Inactividad | Sin peticiones (salvo `/health` y `/events`) ni trabajos durante `api.idle_minutes` | `runtime/idle.py` |

### Hallazgos de la exploración

- **Puerto aleatorio**: `pick_free_port` en `server/src/content_studio/cli/serve.py`.
- **Token por arranque**: `new_token` y `ServerState::connect` en `client/src-tauri/src/lib.rs`.
- **Server dentro del Job**: `server::job::KillOnClose::assign` en `lib.rs`.
- **Línea `ready`**: `ready_line` en `serve.py` y `parse_ready` en `client/src-tauri/src/server.rs`.
- **`/health` existe** (`api/routes/health.py`) y no exige más que el token.
- **Exclusiones de puertos de este equipo** (medido el 2026-11-24): 4252–4351, 5148–5247, 12270–12369, 27581–28480, 50000–50059 y otros; 41830 queda fuera.

## 3. Solución

- Paquete `runtime/` (stdlib) con descubrimiento, token, lock e inactividad.
- `studio api up|status|down|token` y `serve` con puerto fijo, lock y apagado.
- Tauri se adjunta con `studio api up` y deja de ser dueño del proceso; el client se reconecta solo.
- Ajustes > Integraciones.

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: Puerto fijo configurable con respaldo** — El usuario pidió un puerto que no choque y que se pueda cambiar. 41830 no figura en el registro de IANA (consultado el 2026-11-24) ni en las exclusiones de este equipo (`netsh int ipv4 show excludedportrange`). Hyper-V reserva bloques que cambian al reiniciar, por eso el respaldo. Se descarta solo puerto aleatorio con archivo (como Jupyter), porque Stream Deck o Power Automate necesitan una URL fija; y 8000/8080, que ya usan otros servidores.
- **D-2: Archivos junto a la base** — La carpeta ya separa checkout, instalación y `CONTENT_STUDIO_HOME` aislado (`paths.py`), así que cada instalación tiene su server. El token aparte no viaja en el JSON que se lee para descubrir. Se descarta el registro de Windows, porque no existe en POSIX ni en la CI.
- **D-3: Token persistente** — Hoy Tauri genera uno por arranque (`new_token` en `lib.rs`): cualquier cliente externo tendría que reconfigurarse cada vez. Se descarta un token por cliente ya en esta spec, porque solo la LAN lo necesita (032).
- **D-4: Lock de archivo** — `msvcrt.locking` y `fcntl.flock` son stdlib y el SO suelta el lock si el proceso muere; con `api.json` solo, dos arranques simultáneos crearían dos servers. Se descarta mutex con nombre de Windows por ctypes, porque no sirve en POSIX.
- **D-5: Apagado por inactividad** — El usuario lo pidió así; la ventana abierta mantiene un SSE, por eso `/events` no cuenta como uso. Se descarta no apagar con la ventana abierta, que el usuario descartó.
- **D-6: Server independiente de la ventana** — Un MCP o un script pueden estar usándolo; el Job `KillOnClose` (`lib.rs`) lo mataría al cerrar. Se descarta mantener el Job y arrancar otro server para los clientes externos, porque serían dos workers sobre la misma cola.
- **D-7: Guarda de Host** — Con un puerto fijo, una página web podría intentar DNS rebinding; el token ya lo frena, y la guarda es una línea de Starlette. Se descarta nada, porque el puerto fijo lo vuelve predecible.

## 4. Fuera de alcance

- LAN y tokens por dispositivo (032).
- El MCP (029) y la carpeta caliente (030), que usan este server.
- Arrancar con Windows (031).
- Varios usuarios de Windows compartiendo un server.

## 5. Criterios de aceptación

- **AC-1**: WHEN `studio api up` corre sin server THEN arranca uno sin ventana en `api.port` (41830), escribe `api.json` y `api-token`, imprime la línea `ready` y sale con 0.
- **AC-2**: Given un server vivo When se corre `studio api up` (también dos a la vez) Then devuelven la misma URL y sigue habiendo un solo proceso.
- **AC-3**: Given el puerto configurado ocupado When arranca el server Then usa uno libre, lo escribe en `api.json` y lo avisa en `logs/server.log`.
- **AC-4**: WHEN el server se reinicia THEN el token es el mismo; WHEN se corre `studio api token --rotate` THEN el anterior recibe 401.
- **AC-5**: Given `api.idle_minutes` = 1 When pasa más de un minuto sin peticiones ni trabajos Then el server sale y borra `api.json`; con un trabajo en cola o corriendo, no sale.
- **AC-6**: WHEN `studio api down` corre con un trabajo corriendo THEN sale con 1 y no lo detiene; con `--force`, lo cancela y detiene el server.
- **AC-7**: Given un server vivo When se abre la ventana Then se conecta a él sin lanzar otro; WHEN se cierra la ventana THEN el server sigue vivo.
- **AC-8**: Given la ventana abierta y el server apagado por inactividad When el usuario hace una acción que llama a la API Then el server se reactiva, la acción se completa y los eventos SSE vuelven a llegar.
- **AC-9**: Given un server de otra versión When se abre la app Then lo detiene si no hay trabajos y arranca el de su versión; el updater detiene el server antes de instalar.
- **AC-10**: WHEN una petición llega con `Host: evil.example:41830` THEN responde 400 `error.host_not_allowed`.
- **AC-11**: WHEN se abre Ajustes > Integraciones THEN se ven la URL, el puerto y los minutos editables, «Copiar token» y «Cambiar token» con confirmación, en los tres idiomas.

## 6. Debe sonar / no debe sonar

No aplica: la spec no cambia cómo se genera el audio.

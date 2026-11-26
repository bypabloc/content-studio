# Integraciones locales: MCP, API estable, carpeta caliente y Windows (noviembre de 2026)

> Implementado en las specs 025 a 032 (lote cerrado por la 033, 2026-11-25). El estado vigente está en [`docs/process/01-done/integrations.md`](../../process/01-done/integrations.md).

Investigación del 2026-11-24. La pregunta: cómo pueden otras apps de la PC, los LLM y agentes locales y otros equipos de la LAN pedirle trabajos a content-studio (narrar, música, limpiar, convertir, subtítulos) y recibir el archivo resultante. El server debe poder arrancar bajo demanda con la app cerrada. Las internas de la PC y la LAN están dentro del alcance; el acceso desde internet, no.

**Cómo leer este documento**: §1 es el estado del código (con evidencia del repo); §2 a §6, cada mecanismo con fuentes; §7, la propuesta y las decisiones que necesita su spec. Lo marcado **no verificado** salió de fuentes secundarias o no se pudo leer. Las versiones de PyPI se consultaron el 2026-11-24 con `https://pypi.org/pypi/<paquete>/json`.

## Resumen

| Mecanismo | Para quién | Veredicto |
| :--- | :--- | :--- |
| API HTTP estable (puerto y token persistentes, archivo de descubrimiento) | Scripts, PowerShell, Stream Deck, Power Automate, otras apps | **Base de todo lo demás**. Hoy el puerto y el token cambian en cada arranque y el server muere con la ventana |
| Servidor MCP por stdio (`studio mcp`) | Claude Code, Codex, VS Code, Cursor, Claude Desktop, LM Studio, Jan, AnythingLLM | **Sí**, con herramientas curadas sobre `/jobs`; SDK oficial `mcp` 2.3.0 (Python ≥ 3.10) |
| MCP por Streamable HTTP (`/mcp` en la API) | Open WebUI (solo HTTP) y clientes de la LAN | Después, junto con la LAN |
| Carpeta caliente | Herramientas que solo saben escribir archivos | Sí, con sondeo de stdlib y recibos `.result.json`; solo funciona con el server vivo |
| `content-studio://` y menú contextual | El Explorador y los atajos del usuario | Sí, para abrir la app o encolar con confirmación; no es una API |
| Named pipes / AF_UNIX | — | No: HTTP con token cubre lo mismo y llega a la LAN |
| LAN | Celular u otra PC | Opt-in, tokens por dispositivo con permisos; Tailscale Serve para salir de la casa |
| Túnel público (Cloudflare Tunnel, ngrok) | — | Fuera de alcance: expone voces clonadas y archivos del usuario a internet |

## 1. Estado actual del código

| Hecho | Evidencia |
| :--- | :--- |
| La API escucha en `127.0.0.1` con un puerto que elige el sistema | `pick_free_port` y `serve` en `server/src/content_studio/cli/serve.py` |
| El token lo genera Tauri en cada arranque y se lo pasa con `--token` | `new_token` y `ServerState::connect` en `client/src-tauri/src/lib.rs` |
| El server vive dentro de un Job de Windows con *kill on close*: muere con la ventana | `server::job::KillOnClose` en `client/src-tauri/src/lib.rs` |
| Tauri descubre el puerto leyendo la línea `{"ready": {"port": n}}` de stdout | `ready_line` (`serve.py`) y `parse_ready` (`client/src-tauri/src/server.rs`) |
| CORS solo admite los orígenes de Tauri | `TAURI_ORIGINS` en `server/src/content_studio/api/app.py` |
| Ya existe una API genérica de trabajos: `POST /jobs {kind, params}`, `GET /jobs/{id}`, `/jobs/{id}/outputs`, cancelar y reintentar | `server/src/content_studio/api/routes/jobs.py` |
| 28 tipos de trabajo, todos con `validate(params)` | `SERVICES` en `server/src/content_studio/services/registry.py` |
| Progreso en vivo por SSE (`GET /events`, acepta `?token=`) | `server/src/content_studio/api/events.py` |
| Lectura de archivos limitada a `out/` y a los datos de referencia (403 fuera) | `allowed_file` en `server/src/content_studio/api/paths_guard.py` |
| El CLI `studio` encola en SQLite y corre el trabajo en su propio proceso, sin server | `execute` y `run` en `server/src/content_studio/cli/submit.py` |
| La GPU se coordina entre procesos con un candado, no con el server | `server/src/content_studio/gpu_lock.py` |
| Las «carpetas vigiladas» de la Biblioteca se recorren al abrirla, sin watcher | docstring de `server/src/content_studio/library/scan.py` |
| Python mínimo 3.10 (venv de CosyVoice; CI en 3.10 y 3.12) | `requires-python = ">=3.10"` en `server/pyproject.toml` |

Consecuencias:

* **El CLI ya es una integración local**: un script puede correr `uv run studio narration tts ...` o el `studio.exe` instalado y leer la carpeta de `out/`. No sirve a la LAN ni a los LLM sin shell.
* **La API ya sirve para integrar**, pero nadie de afuera puede encontrarla (puerto aleatorio), el token cambia en cada arranque y desaparece al cerrar la ventana.
* Cualquier puerta nueva debe montarse sobre `/jobs` y `SERVICES`, no duplicar la lógica de cada servicio.

### Restricción de versiones de Python

| Paquete | Última versión | Python | ¿Sirve con el mínimo 3.10? |
| :--- | :--- | :--- | :--- |
| `mcp` (SDK oficial) | 2.3.0 (2026-10-02) | ≥ 3.10 | Sí |
| `fastmcp` | 4.2.5 (2026-11-23) | ≥ 3.11 | **No** |
| `fastapi-mcp` | 0.4.0 (2025-07-28, sin releases desde entonces) | ≥ 3.10 | Sí, pero parece abandonado |
| `watchdog` | 7.1.1 (2026-11-21) | ≥ 3.11 | **No** (6.x sí) |
| `watchfiles` | 1.3.0 (2026-09-21) | ≥ 3.10 | Sí |
| `zeroconf` (mDNS) | 0.154.0 (2026-11-06) | ≥ 3.11 | **No** |

El server corre en su propio venv, no en el de CosyVoice: subir su mínimo a 3.11 sería posible, pero es una decisión de stack (`stack.md` §5) y cambia la CI. Esta propuesta evita las tres dependencias que exigen 3.11.

## 2. API HTTP estable y arranque bajo demanda

### Cómo lo resuelven otros

| App | Descubrimiento | Arranque | Fuente |
| :--- | :--- | :--- | :--- |
| Ollama | Puerto fijo `127.0.0.1:11434`, `OLLAMA_HOST` lo cambia | App de bandeja al iniciar sesión; descarga modelos tras 5 min (`OLLAMA_KEEP_ALIVE`) | [Ollama FAQ](https://docs.ollama.com/faq) |
| LM Studio | Puerto fijo 1234 | `lms daemon up` y `lms server start` (headless) | [LM Studio headless](https://lmstudio.ai/docs/developer/core/headless_llmster) |
| Jupyter | Puerto y token aleatorios en un archivo de conexión del usuario, con permisos restrictivos; el cliente lo encuentra con `find_connection_file` | Un proceso por kernel | [jupyter-client connect.py](https://sources.debian.org/src/jupyter-client/8.6.3-2/jupyter_client/connect.py) |
| OBS WebSocket | Puerto fijo 4455, contraseña activada por defecto | Con OBS abierto | [obs-websocket 5.0.0](https://github.com/obsproject/obs-websocket/releases/tag/5.0.0) |
| Home Assistant | Tokens de larga duración que el usuario crea y revoca | Servicio | [auth API](https://developers.home-assistant.io/docs/auth_api.html) |

### Qué conviene aquí

* **Archivo de descubrimiento** `%LOCALAPPDATA%\Content Studio\api.json` con `url`, `pid`, `version` y `started_at`; el token en un archivo aparte (`api-token`), nunca en el JSON ni en la línea de comandos de un proceso visible. `%LOCALAPPDATA%` es del perfil del usuario; comprobar el ACL con `icacls` (**no verificado**).
* **Puerto**: fijo y configurable (evitar 8000, 8080, 1234, 11434, 8188), con el aleatorio como respaldo si está ocupado; el archivo dice cuál quedó. Los clientes MCP no necesitan el puerto (leen el archivo); los manuales (Stream Deck, Power Automate) sí lo agradecen fijo.
* **Token persistente por instalación**, con `studio api token rotate`. Uno nuevo por arranque obliga a reconfigurar cada cliente.
* **Una sola instancia**: antes de arrancar, leer `api.json` y probar `GET /health`; si responde, conectarse. Un mutex con nombre de Windows (`ctypes`, stdlib) evita la carrera de dos arranques simultáneos.
* **Arranque bajo demanda**: lo hace quien llega primero (la ventana, `studio mcp`, `studio api up`). Hoy Tauri es dueño del proceso y lo mata al cerrar; con esta propuesta, la ventana se **adjunta** al server vivo y solo lo arranca si no hay ninguno.
* **Apagado por inactividad**: con la cola vacía, ningún trabajo corriendo y ningún cliente conectado (SSE o MCP) durante N minutos. Mismo patrón que `llm.idle_seconds` del asistente (`docs/process/01-done/llm.md`).
* **Dos workers sobre la misma cola** no deberían romper nada (`queue.claim` toma el trabajo y la GPU tiene candado), pero la instancia única evita la duda.

### Compatibilidad con formatos ajenos

* **OpenAPI**: FastAPI ya la genera (`studio openapi`, que usa el client); sirve para generar clientes en cualquier lenguaje.
* **`/v1/audio/transcriptions` compatible con OpenAI**: la usan Open WebUI y otros como STT ([Open WebUI STT](https://docs.openwebui.com/features/chat-conversations/audio/speech-to-text/self-hosted-stt)). Es corta y encaja.
* **`/v1/audio/speech`** es síncrona: un TTS largo vence el timeout del cliente. Solo vale para textos cortos con un límite explícito; lo largo va por `/jobs`. Home Assistant necesita además un puente Wyoming ([wyoming-openai](https://pypi.org/project/wyoming-openai/)). Prioridad baja.

## 3. Servidor MCP

### Estado de la especificación

| Tema | Dato | Fuente |
| :--- | :--- | :--- |
| Revisión vigente | **2026-07-28**: quita las sesiones (`Mcp-Session-Id`, `initialize`, el stream GET), cada POST lleva `MCP-Protocol-Version`, `Mcp-Method` y `Mcp-Name`; `roots`, `sampling`, `logging` y HTTP+SSE quedan deprecados | [changelog 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/changelog), [blog](https://blog.modelcontextprotocol.io/posts/2026-07-28/) |
| Transportes | stdio y Streamable HTTP | [transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports.md) |
| HTTP local | DEBE validar `Origin` (403 si no vale), DEBERÍA escuchar en 127.0.0.1 y autenticar todas las conexiones | [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http.md) |
| Autorización | Opcional. En HTTP, `Authorization: Bearer` en cada petición (nunca en la query). En stdio NO se usa OAuth: las credenciales salen del entorno | [authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization.md) |
| Trabajos largos | Las *tasks* salieron del núcleo a la extensión `io.modelcontextprotocol/tasks` (`tasks/get` por sondeo, `tasks/cancel` cooperativo); el soporte en clientes varía y no está verificado | [tasks](https://modelcontextprotocol.io/extensions/tasks/overview), [SEP-2663](https://modelcontextprotocol.io/seps/2663-tasks-extension) |
| Progreso y cancelación | `notifications/progress` con `progressToken`; en stdio se cancela con `notifications/cancelled` y en HTTP cerrando el stream | [progress](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/progress.md), [cancellation](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/cancellation.md) |
| Archivos en el resultado | Texto, imagen, audio, `resource_link` y recurso embebido; `structuredContent` con `outputSchema` | [tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools.md) |
| Riesgo conocido | Los SDK de TypeScript (corregido en 1.24.0), Python y Go venían sin protección contra DNS rebinding activa por defecto | [GHSA-w48q-cv73-mx4w](https://github.com/modelcontextprotocol/typescript-sdk/security/advisories/GHSA-w48q-cv73-mx4w), [CSA 2026-11-09](https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-transport-trust-gap-20261109-csa-style/) |

### Clientes locales (docs oficiales, 2026-11-24)

| Cliente | stdio | Streamable HTTP | Header `Authorization` fijo |
| :--- | :--- | :--- | :--- |
| Claude Code | Sí | Sí | Sí, con `${VAR}` |
| Codex CLI | Sí | Sí | Sí (`bearer_token_env_var`) |
| VS Code (Copilot) | Sí | Sí | Sí |
| Cursor | Sí | Sí | Sí (`${env:NAME}`) |
| Claude Desktop | Sí (y extensiones `.mcpb`) | Solo conectores remotos | Sí |
| LM Studio (≥ 0.3.17) | Sí | Remoto, transporte no nombrado | Sí |
| Jan | Sí | Sí | Sí |
| AnythingLLM | Sí (por defecto) | Sí | Sí |
| Open WebUI | No (vía `mcpo`) | Sí, el único nativo | Sí |
| Ollama | Sin soporte MCP nativo (**no verificado** en fuente oficial) | — | — |
| Goose, Cherry Studio | **No verificado** | — | — |

Fuentes: [Claude Code](https://code.claude.com/docs/en/mcp), [Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [VS Code](https://code.visualstudio.com/docs/agents/reference/mcp-configuration), [Cursor](https://cursor.com/docs/context/mcp), [Claude Desktop MCPB](https://claude.com/docs/connectors/building/mcpb), [LM Studio](https://lmstudio.ai/docs/app/mcp), [Jan](https://docs.jan.ai/agent/mcp), [AnythingLLM](https://docs.anythingllm.com/mcp-compatibility/overview), [Open WebUI](https://docs.openwebui.com/features/extensibility/mcp/).

**stdio cubre a casi todos los clientes locales** y no abre ningún puerto nuevo: el cliente lanza `studio mcp` y este habla con la API por loopback.

### Precedentes

* **VoiceStudio** monta el MCP dentro de su backend (`/mcp/`, Streamable HTTP) más un *shim* stdio que reenvía a HTTP; su modo `files` devuelve rutas en vez de base64 para no llenar el contexto del agente, y una carpeta base es la frontera de lectura y escritura. Detalle en [11-mcp-y-agentes.md](../voicestudio-narracion/herramientas/11-mcp-y-agentes.md).
* **Blender MCP** (comunitario): un add-on abre un socket local y un servidor stdio traduce las herramientas ([blender-mcp-server](https://pypi.org/project/blender-mcp-server/)).
* **ComfyUI** publicó un servidor MCP local el 2026-08-18 ([blog](https://blog.comfy.org/p/open-sourcing-comfy-mcp-on-local); **no leído**).

### Diseño sugerido de herramientas

| Herramienta | Qué hace | Notas |
| :--- | :--- | :--- |
| `list_capabilities` | Tipos de trabajo, motores instalados, voces, estilos y presets | Sale de `/catalog` y `SERVICES` |
| `narrate`, `make_music`, `clean_audio`, `convert_media`, `create_subtitles`, `transcribe` | Encolan un trabajo con parámetros tipados y devuelven `job_id` | Una por servicio útil; el `inputSchema` guía al LLM mejor que un `params` libre |
| `get_job` | Estado, progreso y, al terminar, las rutas de salida | `structuredContent` + `resource_link` con `file:///` |
| `wait_job` | Espera hasta N segundos emitiendo `notifications/progress`; si no terminó, devuelve el estado | Cubre los clientes sin *tasks*; HeartMuLa tarda ~5 min por pista |
| `cancel_job` | Cancela | `destructiveHint` |

* **No exponer** lo administrativo (instalar o desinstalar motores, mover almacenamiento, papelera, `/fs`): un LLM puede recibir una inyección de prompt desde un guion o un subtítulo.
* **Nada de audio en base64**: rutas y `resource_link`.
* **Las rutas de entrada** (un video a limpiar) deben pasar por una guarda como `paths_guard`: carpetas permitidas o archivos que el usuario ya indexó.
* **SDK**: `mcp` 2.3.0 (oficial, Python ≥ 3.10). `fastmcp` 4.x exige 3.11 y `fastapi-mcp` no publica desde julio de 2025; además, convertir toda la API con `from_fastapi` expondría las rutas de administración.
* **VRAM**: un LLM cargado en LM Studio u Ollama más un TTS no caben juntos en 8 GB. El trabajo esperará el candado o desbordará; la herramienta debe avisarlo (`gpu_busy`) en vez de colgarse.

## 4. Carpeta caliente

* **Adobe Media Encoder**: cada carpeta vigilada tiene sus ajustes y deja la salida en `Output/`; solo vigila con AME abierto ([Adobe](https://www.adobe.com/learn/media-encoder/web/create-watch-folder), [Larry Jordan](https://larryjordan.com/articles/adobe-media-encoder-watch-folders/)). HandBrake no tiene una oficial. Hazel, Enfocus Switch, DaVinci Resolve y Compressor: **no verificado**.
* **Detección en Windows**: `ReadDirectoryChangesW` pierde eventos si su búfer se desborda; watchdog 7.1.1 lo reporta con `EventsLostEvent` y exige reescanear ([changelog](https://python-watchdog.readthedocs.io/en/latest/changelog.html)). OneDrive y unidades de red: **no verificado**.
* **Propuesta KISS**: sondeo con stdlib cada 2 s (`os.scandir`), sin dependencia. Para unas decenas de archivos alcanza, y funciona igual en OneDrive y en red.

Estructura sugerida, bajo la carpeta de salidas:

```text
inbox/
├── <preset>/              # p. ej. convert-mp3/, clean/, normalize-youtube/: soltar el medio y listo
├── jobs/                  # <nombre>.job.json con {"kind": ..., "params": ...} (rutas relativas a inbox/)
├── processing/            # lo que está en la cola
├── done/                  # <nombre>.result.json con job_id y rutas de salida
└── failed/                # <nombre>.error.json con code y message del catálogo
```

* Un archivo cuenta como listo cuando su tamaño y su fecha no cambian en dos sondeos seguidos; quien escribe un `.job.json` lo hace en `.part` y renombra.
* Idempotencia: la clave es ruta + tamaño + mtime; un reinicio no lo encola dos veces.
* **Límite**: solo funciona con el server vivo. Con arranque bajo demanda, nadie lo despierta al soltar un archivo; hace falta la ventana abierta, `studio api up` o una tarea programada al iniciar sesión.

## 5. Windows: URI, menú contextual e IPC

| Mecanismo | Cómo | Para qué sirve | Fuente |
| :--- | :--- | :--- | :--- |
| `content-studio://` | `tauri-plugin-deep-link` (2.4.x) + `tauri-plugin-single-instance` con la feature `deep-link`, registrado primero; en Windows el SO lanza un proceso nuevo con la URL y el plugin la reenvía a la instancia abierta | Abrir la app en un trabajo, un ítem de la Biblioteca o un formulario prellenado. **Validar** con lista blanca de acciones y **confirmar** antes de encolar | [Tauri deep linking](https://v2.tauri.app/plugin/deep-linking/), [docs.rs 2.4.9](https://docs.rs/crate/tauri-plugin-deep-link/2.4.9/source/src/lib.rs) |
| Carpeta «Enviar a» | Un acceso directo en `%APPDATA%\Microsoft\Windows\SendTo` que llama a `studio` | Lo más barato: sin registro ni admin | Práctica estándar de Windows |
| Verbo clásico | `HKCU\Software\Classes\*\shell\<verbo>`, sin admin | Aparece en «Mostrar más opciones» | **No verificado** en fuente oficial |
| Menú moderno de Windows 11 | `IExplorerCommand` + paquete *sparse* con identidad y DLL COM | Solo si el menú corto es requisito; desde NSIS por usuario **no verificado** | [Microsoft Learn, 2026-07-16](https://learn.microsoft.com/en-my/WINDOWS/APPS/desktop/modernize/integrate-packaged-app-with-file-explorer) |
| Named pipes | `\\.\pipe\...` con DACL propio (el de por defecto da lectura a Everyone) | Descartado: solo local, riesgo de secuestro del pipe, y HTTP ya está | [Microsoft](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights), [CyberArk](https://www.cyberark.com/resources/home/breaking-docker-named-pipes-systematically-docker-desktop-privilege-escalation-part-1) |

Un URI no arranca el server headless: abre la ventana. Para el arranque bajo demanda está `studio`.

## 6. LAN

| Tema | Recomendación | Fuente |
| :--- | :--- | :--- |
| Activación | Apagada por defecto; interruptor en Ajustes | Ollama abre `0.0.0.0` sin autenticación: el contraejemplo ([FAQ](https://docs.ollama.com/faq)) |
| Bind | A la IP de la LAN elegida, no a `0.0.0.0` sin filtro | — |
| Firewall | Regla solo para el perfil Privado; crearla pide admin y el instalador es por usuario (**no verificado** el aviso que muestra Windows) | [Microsoft](https://learn.microsoft.com/windows/security/operating-system-security/network-security/windows-firewall/rules) |
| Emparejamiento | PIN de 6 dígitos en la app → token propio del dispositivo, revocable | [LocalSend protocol](https://github.com/localsend/protocol) |
| Permisos | Por token: `jobs` (encolar y ver), `files` (descargar salidas), nunca `admin` desde la LAN | VoiceStudio separa las rutas admin ([10-api-local-y-cli.md](../voicestudio-narracion/herramientas/10-api-local-y-cli.md)) |
| TLS | Certificado autofirmado y huella fijada en el emparejamiento (modelo LocalSend y KDE Connect) | [LocalSend](https://github.com/localsend/protocol) |
| Descubrimiento | Mostrar URL y QR en la app; mDNS con `zeroconf` exige Python 3.11 | PyPI |
| Fuera de casa | Tailscale Serve entre tus propios equipos, sin abrir puertos | [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve) |

## 7. Propuesta

Un núcleo y varias puertas, en este orden (cada fila puede ser una spec):

| # | Entrega | Depende de | Habilita |
| :--- | :--- | :--- | :--- |
| 1 | **Server compartido**: arranque bajo demanda (`studio api up`), `api.json` + token persistente, instancia única, apagado por inactividad; la ventana se adjunta en vez de ser dueña | — | Todo lo demás |
| 2 | **`studio mcp`** por stdio con las herramientas de §3 y la guía de configuración para Claude Code, Codex, VS Code, Cursor, LM Studio y Claude Desktop | 1 | LLM y agentes locales |
| 3 | **Carpeta caliente** `inbox/` con presets | 1 | Apps que solo escriben archivos |
| 4 | **Windows**: «Enviar a» y `content-studio://` con confirmación | 1 | El Explorador y los atajos |
| 5 | **LAN**: opt-in, emparejamiento, tokens con permisos, TLS; `/mcp` por Streamable HTTP para Open WebUI y clientes remotos | 1, 2 | Celular y otras PC |

### Decisiones abiertas para la spec

1. ¿Puerto fijo por defecto, y cuál?
2. ¿El apagado por inactividad aplica también cuando la ventana está abierta? (Propuesta: no; con la ventana, el server vive.)
3. ¿Subir el mínimo del server a Python 3.11 para usar `fastmcp`, `watchdog` 7 y `zeroconf`, o quedarse en 3.10 con `mcp` y stdlib? (Propuesta: 3.10.)
4. ¿Herramientas MCP tipadas por servicio o una genérica `submit_job(kind, params)`? (Propuesta: tipadas para lo frecuente y la genérica para el resto.)
5. ¿Qué carpetas de entrada se permiten a un cliente externo? (Propuesta: las de la Biblioteca y `inbox/`.)
6. ¿La carpeta caliente vive en la carpeta de salidas o en una que elige el usuario?

## Fuera de alcance

* Exponer el server a internet (Cloudflare Tunnel, ngrok): el usuario pidió PC y LAN.
* Ser cliente de LLM externos: el asistente local ya existe (`docs/process/01-done/llm.md`).
* Servicio de Windows (SCM) que corra antes del inicio de sesión: los motores y modelos viven en el perfil del usuario.

# Spec 029: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `029-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-029/` o `tmp/spec-029/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'feature/028-shared-server' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/runtime/instance.py || echo FALLA
uv pip index versions mcp   # la última versión del SDK
```

## 2. Contexto

Con la 028, el server compartido arranca bajo demanda y deja su dirección y su token en archivos conocidos. Los LLM y agentes locales no hablan HTTP por su cuenta: hablan MCP. Hoy no hay ningún servidor MCP en el repo.

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Bridge | El proceso `studio mcp` que lanza el cliente MCP y que traduce las herramientas a la API | `mcp_server/bridge.py` |
| Herramienta | Una función MCP con `inputSchema` y `outputSchema` | `mcp_server/tools.py` |
| `resource_link` | Bloque de resultado MCP que apunta a un recurso por URI | MCP, `tools` 2025-11-25 |

### Hallazgos de la exploración

- **API de trabajos genérica**: `POST /jobs {kind, params}` valida con el `validate` de cada servicio y devuelve 422 con `errors` (`api/routes/jobs.py`, `create_job`).
- **Salidas por trabajo**: `GET /jobs/{id}/outputs` lista audio y video de `output_dir` (`api/routes/jobs.py`, `job_outputs`).
- **Catálogos**: `GET /catalog/{kind}` (`api/routes/catalog.py`) y `/voices/profiles` (`api/routes/voices.py`).
- **Candado de GPU**: `server/src/content_studio/gpu_lock.py` dice quién lo tiene.
- **Spec MCP 2026-07-28**: sin sesiones; *tasks* como extensión; autorización opcional y, en stdio, credenciales del entorno (investigación §3).
- **SDK**: `mcp` 2.3.0 (2026-10-02, Python ≥ 3.10); `fastmcp` 4.2.5 exige 3.11 (PyPI, 2026-11-24).

## 3. Solución

- `content_studio/mcp_server/` con las herramientas (sin SDK), el bridge stdio y los fragmentos de configuración.
- `studio mcp` y `studio mcp config`; `GET /integrations/mcp-config` para la app.
- En Ajustes > Integraciones, copiar la configuración por cliente.
- Guía `docs/operations/mcp.md` con cada cliente.

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: stdio con el SDK oficial** — stdio lo soportan casi todos los clientes locales (investigación §3) y no abre otro puerto; la spec de MCP dice que en stdio las credenciales salen del entorno, así que el bridge lee `api-token` solo. `mcp` 2.3.0 es oficial y corre en la Python del server. Se descarta `fastmcp` (más dependencias, no hace falta con el SDK) y `fastapi-mcp` (sin releases desde 2025-07 y expone toda la API).
- **D-2: Herramientas curadas** — La guía de Anthropic y la experiencia de VoiceStudio recomiendan pocas herramientas por tarea; los modelos locales eligen peor con listas largas. La genérica cubre los 28 tipos sin una herramienta por cada uno. Se descarta una por servicio (28), que satura a los modelos chicos; y solo la genérica, con la que el LLM tendría que adivinar los `params`.
- **D-3: Esperar con progreso** — La extensión `io.modelcontextprotocol/tasks` salió del núcleo en la revisión 2026-07-28 y su soporte en los clientes no está verificado; HeartMuLa tarda ~5 min por pista. Se descarta *tasks* como único camino, porque dejaría afuera a los clientes que no la soportan.
- **D-4: Salidas por archivo** — Un WAV en base64 llena el contexto del agente (VoiceStudio tuvo que agregar el modo `files`). Se descarta recursos embebidos, por el mismo motivo.
- **D-5: Rutas de entrada del sistema** — El usuario lo pidió: los clientes locales ya tienen acceso a sus archivos. Se descarta limitar a la Biblioteca, que el usuario descartó.
- **D-6: Superficie mínima** — Un texto de entrada puede traer instrucciones escondidas (inyección de prompt); lo destructivo se hace en la app. Se descarta exponer todo con `from_fastapi`, descartado en la investigación.

## 4. Fuera de alcance

- MCP por Streamable HTTP y clientes de la LAN (032).
- *tasks* de MCP (D-3); cuando los clientes las soporten va a `docs/process/03-later/`.
- Herramientas administrativas (D-6).
- Recursos y prompts MCP: solo herramientas.

## 5. Criterios de aceptación

- **AC-1**: WHEN un cliente MCP lista las herramientas de `studio mcp` THEN recibe exactamente las diez de 02 §2, cada una con `inputSchema` y `outputSchema`, y ninguna administrativa.
- **AC-2**: Given el server apagado When llega la primera llamada a una herramienta Then el bridge arranca el server compartido y la llamada responde.
- **AC-3**: WHEN se llama `studio_narrate` con texto y voz y luego `studio_wait_job` THEN el resultado trae `status: done`, las rutas de salida existentes y un `resource_link` `file:///` por archivo, sin base64.
- **AC-4**: WHEN una herramienta recibe una ruta de entrada que no existe THEN responde `isError: true` con `input_not_found` y la ruta; con una ruta existente fuera de `out/`, encola.
- **AC-5**: Given un `progressToken` When `studio_wait_job` espera un trabajo que avanza Then emite `notifications/progress` crecientes y, si vence `timeout_s`, devuelve el estado actual sin error.
- **AC-6**: WHEN se llama `studio_cancel_job` sobre un trabajo corriendo THEN el trabajo termina `cancelled` y su proceso ya no existe.
- **AC-7**: Given otra sesión con el candado de la GPU When se consulta un trabajo de GPU en cola Then `status` es `waiting_gpu` y `waiting_on` dice quién la tiene.
- **AC-8**: WHEN `studio_submit_job` recibe un `kind` desconocido o `params` inválidos THEN responde `isError: true` con los errores de validación del servicio.
- **AC-9**: WHEN se corre `studio mcp config --client <c>` para cada cliente de 02 §3 THEN imprime un fragmento válido para ese cliente (JSON o TOML que se parsea) con la ruta de `studio`, sin token.
- **AC-10**: WHEN se abre Ajustes > Integraciones y se elige un cliente THEN «Copiar configuración» copia el mismo fragmento, en los tres idiomas.
- **AC-11**: WHEN Claude Code y Codex CLI se configuran con ese fragmento y se les pide «narra este texto con la voz <v>» THEN el archivo aparece en `out/narration/` y el agente devuelve su ruta.

## 6. Debe sonar / no debe sonar

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| Narración pedida desde Claude Code (`out/narration/<…>-spec-029/`) | Igual a la de `studio narration tts` con los mismos parámetros (duración ±5 %, LUFS ±0,5 LU) | Cortes o un texto distinto al pedido |

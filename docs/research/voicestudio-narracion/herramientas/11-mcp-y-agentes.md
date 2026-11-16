# Servidor MCP y Agentes

> Investigación del 2026-11-15. Cubre el servidor MCP de VoiceStudio (herramientas, recursos, modos de salida, conexión a Claude Code), las voces por agente, las skills para agentes, la "voz agéntica" (pipecat, LiveKit, OpenAI Agents SDK) y los proveedores LLM. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Fuente principal: clon local del repo `debpalash/VoiceStudio` (commit `80b4594`, 2026-11-16). Rutas relativas a la raíz del repo.

---

## 1. Qué Es

- Un servidor [MCP](https://modelcontextprotocol.io/) **montado en el backend** en `http://localhost:3900/mcp/` (Streamable HTTP). Con la app abierta no hay que arrancar nada más. **(leída)** `docs/mcp.md`; código en `backend/mcp_server.py` (`create_mcp_server` l. 782, `mount_mcp` l. 1289).
- Las herramientas llaman a la API REST del backend (p. ej. `generate_speech` → `POST /generate`). **(leída)** `backend/mcp_server.py` l. 924-1006.
- Para clientes solo stdio hay un shim (`python -m backend.mcp_shim`) que reenvía a HTTP, y un servidor stdio directo (`uv run python -m backend.mcp_server`). Ambos necesitan un checkout del repo. **(leída)** `docs/mcp.md` §"stdio".
- "Voz agéntica": VoiceStudio actúa como **proveedor** TTS/STT compatible con OpenAI; el orquestador lo pones tú. **(leída)** `docs/agentic-voice.md`.

## 2. Cómo Se Usa

### 2.1 Conectar Claude Code

Opción A, HTTP (recomendada). Archivo `.mcp.json` que exporta la app en **Integrations → Claude Code** **(leída)** `electron/src/renderer/src/features/integrations/mcp-setup.ts`:

```json
{
  "mcpServers": {
    "voicestudio": {
      "type": "http",
      "url": "http://127.0.0.1:3900/mcp/",
      "headers": { "X-OmniVoice-Client-Id": "claude-code" }
    }
  }
}
```

Equivalente por terminal de Claude Code (sintaxis de Claude Code, no del repo; **no verificado** contra VoiceStudio en ejecución):

```bash
claude mcp add --transport http voicestudio http://127.0.0.1:3900/mcp/ \
  --header "X-OmniVoice-Client-Id: claude-code"
```

Opción B, stdio vía shim **(leída)** `docs/mcp.json`:

```json
{
  "mcpServers": {
    "omnivoice": {
      "command": "python",
      "args": ["-m", "backend.mcp_shim"],
      "cwd": "/path/to/VoiceStudio",
      "env": { "OMNIVOICE_PORT": "3900", "OMNIVOICE_CLIENT_ID": "claude-code" }
    }
  }
}
```

- Conserva la barra final `/mcp/`: funciona en todas las versiones; `/mcp` sin barra daba 405 en builds viejos. **(leída)** `docs/mcp.md`.
- Para un backend remoto con HTTPS, la exportación referencia la clave como `Bearer ${OMNIVOICE_API_KEY}`; nunca la incrusta. A un backend remoto en HTTP plano no le pone clave. **(leída)** `mcp-setup.ts` l. 36-45 y 85-92.

### 2.2 Voz por agente

Cada cliente se identifica con `X-OmniVoice-Client-Id`. Precedencia en `generate_speech`: `profile_id` explícito → binding del cliente → voz por defecto. **(leída)** `docs/mcp.md` §"Per-agent voices", `backend/mcp_server.py` l. 965-973.

```bash
curl localhost:3900/api/mcp/bindings
curl -X PUT localhost:3900/api/mcp/bindings -H 'Content-Type: application/json' \
  -d '{"client_id":"claude-code","label":"Claude Code","profile_id":"<voice-profile-id>"}'
curl -X DELETE localhost:3900/api/mcp/bindings/claude-code
# o con la CLI:
voicestudio integrations mcp bindings set claude-code --voice "Mi voz"
```

Rutas en `backend/api/routers/mcp_bindings.py` (prefijo `/api/mcp`, l. 16-49) **(leída)**; son admin (loopback o API key) según `docs/api-auth.md`.

### 2.3 Sacar el audio del contexto del agente

Por defecto `generate_speech` devuelve el WAV en base64 dentro de la respuesta (caro en tokens). Para agentes LLM conviene modo archivos **(leída)** `docs/mcp.md` §"Output mode":

```bash
# en el entorno del BACKEND (no del cliente MCP)
OMNIVOICE_MCP_OUTPUT_MODE=files
OMNIVOICE_MCP_BASE_PATH=/ruta/compartida/con/el/agente
```

Así la herramienta devuelve `audio_url` (`/audio/<id>.<fmt>`) y `output_path` dentro del base path. El base path es además la frontera de seguridad para `transcribe(audio_path=…)` y `clone_voice(ref_audio_path=…)`: sin él, las rutas se rechazan.

## 3. Opciones y Parámetros

Herramientas expuestas **(leída)** `backend/mcp_server.py` l. 924-1287 y `docs/mcp.md`:

| Herramienta / recurso | Parámetros | Devuelve |
| :--- | :--- | :--- |
| `generate_speech` | `text`, `language`, `profile_id`, `instruct`, `speed=1.0`, `steps=16` (8 borrador, 16 balance, 32 calidad), `format` (`wav`/`ogg`/`opus`) | JSON con `audio_id`, `generation_time_s`, `audio_duration_s` y audio según el modo de salida |
| `clone_voice` | `name`, `ref_audio_base64` o `ref_audio_path`, `ref_text`, `instruct`, `language="Auto"` | `profile_id` |
| `describe_voice` | `description` | Mapeo a género, edad, tono, estilo, acento; lista `unmatched` |
| `design_voice` | `name`, `description`, `language="Auto"` | `profile_id` de voz diseñada (semilla fija) |
| `transcribe` | `audio_base64` o `audio_path`, `language` | Texto (JSON) |
| `list_voices`, `list_personalities`, `list_languages` | — | JSON en texto |
| `check_health` | — | Estado y dispositivo GPU |
| recurso `voice://{profile_id}` | — | Perfil en JSON |
| recurso `history://recent` | — | Últimas ≤ 20 generaciones |

Variables de entorno **(leída)** `docs/mcp.md`:

| Variable | Valores | Efecto |
| :--- | :--- | :--- |
| `OMNIVOICE_MCP_OUTPUT_MODE` | `resources` (default), `files`, `both` | Base64 inline, URL + archivo, o ambos |
| `OMNIVOICE_MCP_BASE_PATH` | directorio | Frontera de lectura/escritura de archivos |
| `OMNIVOICE_MCP_TIMEOUT_S` | segundos | Espera fija; si no, sigue al backend (mín. 120 s) |
| `OMNIVOICE_MCP_ALLOWED_HOSTS` | lista de hosts | Para Docker/LAN (guarda anti DNS-rebinding) |
| `OMNIVOICE_MCP_DISABLE=1` | — | No monta `/mcp` |
| `OMNIVOICE_CLIENT_ID`, `OMNIVOICE_HOST`/`OMNIVOICE_URL`, `OMNIVOICE_API_KEY` | — | Shim stdio |

Limitaciones del código:

- `generate_speech` **no** tiene parámetro `engine` ni `seed`: usa el motor activo y no es reproducible por semilla desde MCP. **(leída)** firma l. 925-933.
- El acento de `describe_voice`/`design_voice` solo cubre acentos de inglés y dialectos chinos; "español neutro" no es un atributo de diseño. **(leída)** docstring de `describe_voice`.
- `list_languages` devuelve una lista fija de 20 idiomas populares y la cifra 646. **(leída)** l. 1028-1041.

## 4. Ejemplos

Pedido típico desde Claude Code una vez conectado (flujo **no verificado** en ejecución):

1. `list_voices` → elegir `profile_id`.
2. `generate_speech(text="Hola, hoy vemos…", language="es", profile_id="<id>", steps=32)`.
3. Con `OMNIVOICE_MCP_OUTPUT_MODE=files`, recibir `output_path` y pasarlo a ffmpeg.

Configuración para Codex CLI **(leída)** `docs/mcp.md`:

```toml
[mcp_servers.voicestudio]
url = "http://127.0.0.1:3900/mcp/"
http_headers = { "X-OmniVoice-Client-Id" = "codex-cli" }
```

pipecat como proveedor TTS/STT **(leída)** `docs/agentic-voice.md`, ejemplo ejecutable en `examples/agentic/pipecat_minimal.py`:

```python
from pipecat.services.openai.tts import OpenAITTSService
tts = OpenAITTSService(base_url="http://localhost:3900/v1", api_key="not-needed-locally",
                       voice="<your-voice-profile-id>", model="omnivoice", sample_rate=24000)
```

Skill para agentes: `skills/voicestudio/SKILL.md` **(leída)** le dice al agente: comprobar `GET /health`, descubrir contratos en `GET /openapi.json` y voces en `GET /v1/audio/voices`, no inventar ids, verificar el archivo antes de decir "listo", y no instalar modelos ni pasar a un proveedor en la nube sin permiso. La comunidad cita su instalación como `npx skills add debpalash/VoiceStudio` **(snippet)** [everydev.ai](https://www.everydev.ai/tools/voicestudio). `skills/voicestudio-maintainer/SKILL.md` es para mantener el repo, no para usar audio. `.agents/skills/` (fastapi-python, vite) son guías genéricas de desarrollo **(leída)**.

Proveedores LLM **(leída)** `docs/electron-llm-providers.md`: la app usa un LLM para limpiar dictado, traducir y el agente de llamadas. Transportes: SDK compatible con OpenAI (OpenAI, Gemini, Mistral, OpenRouter…), LiteLLM nativo (Anthropic, Bedrock, Vertex) o **CLI instalada** (Claude Code, Codex, Pi, OpenCode con su login). Setup local verificado: Ollama `http://127.0.0.1:11434/v1` con `qwen3:4b-instruct-2507-q4_K_M`.

## 5. Tips y Trucos

- Usa modo `files` + base path compartido: evita meter WAV en base64 en el contexto del agente. **(leída)** `docs/mcp.md`, `docs/mcp.json`.
- `format="ogg"`/`"opus"` solo funciona en modo `files` o `both` y requiere ffmpeg. **(leída)** `backend/mcp_server.py` l. 954-960.
- La primera `generate_speech` en una máquina sin el modelo descarga ~2.3 GB dentro del presupuesto de tiempo; instálalo antes. **(leída)** `docs/mcp.md`.
- Una conexión HTTP (incluido el shim) **no** hereda permisos de operador: puede generar, clonar y diseñar, pero no editar ni borrar perfiles. **(leída)** `docs/mcp.md` §"Streamable HTTP".
- El transporte MCP no está autenticado por sí mismo: no lo expongas fuera de una LAN de confianza o un túnel TLS. **(leída)** misma fuente.
- Prefiere un perfil marcado como **voz propia verificada** para cualquier agente que hable "como tú". **(leída)** `docs/mcp.md`, `docs/agentic-voice.md`.
- **conflicto**: la CLI genera para Codex el client id `"codex"` y para Claude Code un `.mcp.json` **sin** `"type": "http"` (`cli/voicestudio_cli/__main__.py` l. 677-683), mientras la app y la doc usan `"codex-cli"` y sí incluyen `"type": "http"` (`mcp-setup.ts`). Si se usa `voicestudio integrations mcp config`, revisar ambos campos. Impacto real en Claude Code **no verificado**.

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#3944](https://github.com/debpalash/VoiceStudio/issues/3944) | cerrado | Las herramientas MCP ocultaban el detalle del backend (`transcribe` daba un 403 pelado en vez del aviso de licencia). **(leída)** |
| [#2347](https://github.com/debpalash/VoiceStudio/issues/2347) | cerrado | Pedido de acceso LAN a `/mcp`; hoy existe vía PIN + `OMNIVOICE_MCP_ALLOWED_HOSTS`. **(leída)** |
| [#2568](https://github.com/debpalash/VoiceStudio/issues/2568) | cerrado | Ediciones parciales concurrentes de bindings se pisaban. **(snippet)** solo título. |
| [#2646](https://github.com/debpalash/VoiceStudio/issues/2646) | cerrado | Herramienta MCP de reparación bufferizaba respuestas antes de aplicar el límite. **(snippet)** |
| [#2428](https://github.com/debpalash/VoiceStudio/issues/2428) | cerrado | Con LLMs de razonamiento que prellenan `<think>`, el agente de llamadas leía el razonamiento en voz alta. **(leída)** |

## 7. Qué Dice la Comunidad

- **B** — [andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) (sep-2026, updates nov): describe `localhost:3900/mcp` con `generate_speech`, `clone_voice`, `transcribe` y config JSON para Claude Desktop y Cursor; cita a un usuario de r/LocalLLaMA con 25-30 s para 15 s de audio en una RX 590 y concluye que no sirve para agentes conversacionales en tiempo real en hardware modesto.
- **B** — [remio.ai](https://www.remio.ai/post/debpalash-voicestudio-hit-github-trending-but-local-voice-ai-still-has-to-prove) (sep-2026): MCP permite que un agente genere voz o transcriba sin salir de la máquina; el proyecto sigue en beta.
- **C** — [tessl.io](https://tessl.io/registry/skills/github/debpalash/OmniVoice-Studio/omnivoice) lista la skill con licencia FSL-1.1-ALv2, en **conflicto** con AGPL-3.0 del repo actual (`cli/pyproject.toml`). Probablemente refleja una versión vieja (OmniVoice-Studio). **no verificado**.
- Alternativas MCP de voz más pequeñas para Claude Code (Kokoro, Supertonic): [soliloquy-tts](https://pypi.org/project/soliloquy-tts/0.2.6/), [voice-mcp](https://glama.ai/mcp/servers/jochiang/voice-mcp). **(snippet)** C.

## 8. Qué Sirve para social-videos

**¿Conviene que Claude Code genere narraciones vía MCP?** Sí como idea, pero con un servidor propio y mínimo, no con VoiceStudio:

1. **Hoy no hace falta MCP.** Claude Code ya puede ejecutar `python narration/tts.py ...` por Bash. MCP agrega valor solo si se quiere: (a) un modelo caliente en memoria entre peticiones (evita recargar Qwen3-TTS en cada frase), (b) un contrato tipado que el agente descubra solo, y (c) resultados en JSON en vez de texto de consola.
2. **Diseño a copiar (no el código AGPL):**
   - Herramienta `generar_narracion(texto, estilo, ref, idioma, seed)` que devuelva **ruta de archivo + duración + seed**, nunca base64 (lección del modo `files`).
   - Una **carpeta frontera** (`out/narration/`) fuera de la cual no se lee ni escribe (lección de `OMNIVOICE_MCP_BASE_PATH`).
   - Herramientas de descubrimiento `listar_voces` y `listar_estilos` para que el agente no invente nombres (lección de la skill).
   - Devolver el **error real** del script al agente (lección de #3944).
   - Aceptar `seed` y `modelo`, que el MCP de VoiceStudio no expone.
3. **Regla 2 del proyecto** (un modelo a la vez en 8 GB): un servidor MCP residente debe liberar VRAM al terminar o tener un apagado por inactividad, como la CLI de VoiceStudio (10 min, `VOICESTUDIO_IDLE_SHUTDOWN_S`).
4. **Alternativa más barata:** una skill de Claude Code (`.claude/skills/narrar/SKILL.md`) que describa cómo invocar `tts.py`, qué verificar (duración, volumen, espectrograma) y que no se declare "listo" sin revisar el WAV. Es la misma idea que `skills/voicestudio/SKILL.md` y no requiere servidor.
5. Si en algún momento se usa VoiceStudio tal cual como motor externo, su MCP no permite elegir motor ni seed y su `design_voice` no conoce acentos en español; para narración en español neutro habría que usar perfiles clonados por `profile_id`.

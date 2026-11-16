# API Local y CLI

> Investigación del 2026-11-15. Cubre la API HTTP/WebSocket de TTS de VoiceStudio (`POST /generate`, streaming NDJSON, `/ws/tts`, `/v1/audio/speech` compatible con OpenAI), su autenticación y el comando de terminal `voicestudio`. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Fuente principal: clon local del repo `debpalash/VoiceStudio` (commit `80b4594`, 2026-11-16). Rutas relativas a la raíz del repo. No se ejecutó la app: todo sale de leer código y docs.

---

## 1. Qué Es

- El backend FastAPI escucha en `http://127.0.0.1:3900` y expone tres superficies de TTS **(leída)**:
  - **Nativa** `POST /generate` (multipart/form), con todos los controles del motor. `backend/api/routers/generation.py` l. 1902.
  - **Compatible con OpenAI** `POST /v1/audio/speech` (JSON), para usar el SDK `openai` o cualquier cliente que ya hable ese formato. `backend/api/routers/openai_compat.py` l. 847.
  - **WebSocket** `/ws/tts` para audio PCM en vivo. `backend/api/routers/tts_stream.py` l. 346.
- La misma API sirve transcripción (`/v1/audio/transcriptions`, `/v1/audio/translations`) y descubrimiento (`/.well-known/voicestudio-speech`, `/v1/models`, `/v1/audio/voices`). **(leída)** `docs/agentic-voice.md`.
- **CLI** `voicestudio`: paquete `voicestudio-cli` (Python ≥ 3.11, sin dependencias, AGPL-3.0-only) que abre la app o habla con su backend por HTTP. 160 comandos del registro más ~45 escritos a mano. **(leída)** `cli/pyproject.toml`, `cli/voicestudio_cli/contracts.json`, `cli/voicestudio_cli/__main__.py`.

## 2. Cómo Se Usa

### 2.1 Autenticación (resumen)

Por defecto el backend es **solo loopback y sin autenticación**: un script local no necesita clave. **(leída)** `docs/api-auth.md`.

| Puerta | Se activa con | Cubre |
| :--- | :--- | :--- |
| PIN de 6 dígitos | toggle de red compartida en la app | HTTP no-loopback (no WebSockets) |
| API key | variable `OMNIVOICE_API_KEY` en el backend | HTTP y WebSocket no-loopback; se envía como `Authorization: Bearer <key>` |
| Redes confiables | `OMNIVOICE_TRUSTED_NETWORKS` (CIDR) | exime de las dos anteriores solo en rutas de consumo |

- Admin (`/system/*`, `/api/settings/*`, selección/instalación de motores, bindings MCP) exige loopback real o la API key; el PIN nunca alcanza. **(leída)** `docs/api-auth.md` §"Admin routes".
- La API key es una credencial raíz, no un token por ruta. Para producción: Docker con `127.0.0.1:3900:3900`, versión fijada y proxy con lista blanca de rutas. **(leída)** `docs/production-private-api.md`.

### 2.2 `POST /generate` (nativo)

Campos de formulario reales **(leída)** `backend/api/routers/generation.py` l. 1903-1953: `text` (obligatorio), `language`, `ref_audio` (archivo), `ref_text`, `instruct`, `duration`, `num_step`, `guidance_scale=2.0`, `speed=1.0`, `t_shift`, `denoise=true`, `profile_id`, `seed`, `effect_preset="broadcast"`, `wav_bits` (`16`/`24`/`32`), `engine`, `preset_voice`, `max_chunk_chars=800`, `crossfade_ms=50`, `pronounce=true`, `stream=false`, más controles de emoción para IndexTTS2 (`emo_text`, `emo_alpha`, `emo_vector`, `emotion`).

- Respuesta clásica: WAV con cabeceras `X-Audio-Id`, `X-Gen-Time`, `X-Audio-Duration` (l. 2811-2815) y, si hubo ruteo, `X-OmniVoice-Routing` (l. 1847). Si se perdieron trozos: `X-OmniVoice-Dropped-Chunks` (l. 2823).
- Con `stream=true` la respuesta es `application/x-ndjson`, una línea JSON por evento (l. 2563-2687):

```json
{"type":"start","sample_rate":24000,"channels":1,"format":"pcm16","total_chunks":3,"crossfade_ms":50,"seed":123}
{"type":"chunk","seq":0,"pcm":"<base64 PCM16>"}
{"type":"warning","code":"dropped_chunks","count":1,"text":["..."]}
{"type":"done","id":"...","audio_path":"...","duration":7.4,"gen_time":2.1,"seed":123,"sample_rate":24000,"dropped_chunks":0}
{"type":"error", "...": "..."}
```

  El WAV final en disco sale del mismo camino que la versión clásica: el streaming es solo un canal de entrega con troceo por texto, no streaming por tokens del motor (comentario l. 1945-1952). Valores de ejemplo del bloque anterior: **no verificado** (los nombres de campos sí están leídos).

### 2.3 `POST /v1/audio/speech` (OpenAI)

Modelo `SpeechRequest` **(leída)** `backend/api/routers/openai_compat.py` l. 244-363:

- `model` (default `omnivoice`): id de motor instalado o alias OpenAI (`tts-1`, `tts-1-hd`, `gpt-4o-mini-tts`) que apunta al motor activo.
- `input` (≤ 4096 caracteres), `voice` (id o nombre de perfil, `default`, preset, o nombre OpenAI como `alloy`, que mapea a la voz por defecto del motor).
- `response_format`: `mp3` (default), `opus`, `aac`, `flac`, `wav`, `pcm` (24 kHz s16le mono). mp3/opus/aac requieren ffmpeg.
- `speed` 0.25-4.0, `stream_format` `audio` o `sse`, `instructions`.
- Extensiones VoiceStudio: `language`, `description`, `instruct`, `duration`, `seed`, `denoise`, `preprocess_prompt`, `chunk_duration`, `chunk_threshold`, `num_step` (1-128), `guidance_scale` (0-20).
- Errores con forma OpenAI `{"error":{"message","type","param","code"}}` más `detail`. **(leída)** `docs/agentic-voice.md`.

### 2.4 `/ws/tts` (WebSocket)

Protocolo **(leída)** `backend/api/routers/tts_stream.py` docstring y `StreamTTSRequest` (l. 85-104):

- Cliente envía JSON: `text`, `voice` (profile_id o preset), `language`, `speed`, `duration_factor` (IndexTTS 2.5), `instruct`, `description`, `emo_*`, `engine`.
- Servidor envía binario PCM16 24 kHz mono en trozos de 4800 muestras (200 ms; `OMNIVOICE_STREAM_CHUNK`) y al final `{"type":"done","duration_s":…,"gen_time_s":…,"ttfa_ms":…,"rtf":…}` o `{"type":"error","detail":…}`.
- El PIN no autoriza WebSockets; desde otra máquina hace falta API key, sesión admin con ticket (`POST /api/auth/ws-ticket`) o red confiable. **(leída)** `docs/api-auth.md` §"WebSocket access".

### 2.5 CLI `voicestudio`

- Se instala con la app de escritorio (enlaza `~/.local/bin/voicestudio`) o desde un checkout: `PYTHONPATH=cli python3 -m voicestudio_cli.install ./cli`. **(leída)** `docs/install/script.md` §"Terminal command".
- Si la app no corre, un comando que crea o cambia algo (p. ej. `speak`) la arranca **en segundo plano sin ventana**; se apaga tras 10 min inactiva (`VOICESTUDIO_IDLE_SHUTDOWN_S`). Con `--url` o `VOICESTUDIO_URL` usa un backend externo y nunca arranca la app. **(leída)** misma fuente.
- `--json` da salida para scripts; errores en stderr como `{"error":{"code","message"}}`. Códigos de salida: 0 ok, 1 fallo, 2 uso inválido, 3 app no corriendo (`status`). **(leída)** misma fuente.
- `speak` llama a `POST /generate` con `text`, `profile_id` (resuelto desde nombre o id), `speed` y opcionales `engine`, `language`, `seed`, `instruct`; exige `--output`. **(leída)** `cli/voicestudio_cli/__main__.py` l. 792-813.
- La clave se guarda con `voicestudio connection auth set --stdin` en `~/.config/voicestudio-cli/config.json` (o `VOICESTUDIO_CONFIG`). **(leída)** `cli/voicestudio_cli/config.py`.

## 3. Opciones y Parámetros

| Opción | Dónde | Efecto | Fuente |
| :--- | :--- | :--- | :--- |
| `engine` | `/generate`, `/ws/tts`, `speak --engine` | Motor por petición; sin él, el motor activo (o `OMNIVOICE_TTS_BACKEND`) | `generation.py` l. 1962-1970 **(leída)** |
| `max_chunk_chars` / `crossfade_ms` | `/generate` | Trocea texto largo por oraciones (800) y une con crossfade (50 ms); 0 desactiva | `generation.py` l. 1937-1940 **(leída)** |
| `pronounce` + `[[…]]` | `/generate` | Diccionario de pronunciación y overrides inline antes de sintetizar | `generation.py` l. 1941-1945 **(leída)** |
| `seed` | `/generate`, `/v1/audio/speech`, `speak --seed` | Reproducibilidad | `openai_compat.py` **(leída)** |
| `num_step` | `/generate`, `/v1` | 16 por defecto, 32 = preset de calidad | `openai_compat.py` l. 339-345 **(leída)** |
| `effect_preset` | `/generate` | Masterizado; default `broadcast` | `generation.py` l. 1932 **(leída)** |
| `wav_bits` | `/generate` | 16/24/32 bits | `generation.py` l. 1933 **(leída)** |
| `stream` | `/generate` | NDJSON con previews PCM16 base64 | `generation.py` l. 1946-1952 **(leída)** |
| `stream_format` | `/v1/audio/speech` | `audio` (bytes) o `sse` (`speech.audio.delta`/`done`) | `openai_compat.py` l. 293-298 **(leída)** |
| `OMNIVOICE_API_KEY` | backend | Activa la puerta de API key | `docs/api-auth.md` **(leída)** |
| `OMNIVOICE_PORT` | backend/clientes | Puerto (3900) | `docs/speech-platform.md` **(leída)** |
| `OMNIVOICE_GENERATE_TIMEOUT_S` | backend | Presupuesto de generación; el primer uso descarga ~2.3 GB dentro de él | `docs/mcp.md`, issue #1014 **(leída)** |
| `--url`, `--json`, `--timeout` (600 s), `-o`, `--overwrite` | CLI global | Backend, salida y espera | `__main__.py` l. 70-86 **(leída)** |

## 4. Ejemplos

`curl` contra el endpoint OpenAI (loopback, sin clave) **(leída)** `skills/voicestudio/SKILL.md`:

```bash
echo '{"model":"tts-1","voice":"alloy","input":"Every voice has a story.","response_format":"wav"}' > speech-request.json
curl --fail-with-body --show-error http://localhost:3900/v1/audio/speech \
  -H 'Content-Type: application/json' --data-binary @speech-request.json --output speech.wav
```

SDK de OpenAI contra un backend remoto con clave (usar HTTPS) **(leída)** `docs/api-auth.md`:

```python
from openai import OpenAI
client = OpenAI(base_url="https://gpu-box:3900/v1", api_key="<OMNIVOICE_API_KEY>")
audio = client.audio.speech.create(model="tts-1", voice="alloy",
                                   input="Hello from a keyed backend.", response_format="wav")
audio.write_to_file("speech.wav")
```

PCM en streaming con el SDK **(leída)** `docs/agentic-voice.md`:

```python
with client.audio.speech.with_streaming_response.create(
    model="omnivoice", voice="your-voice-profile-id",
    input="The first sentence can play immediately.",
    response_format="pcm", stream_format="audio",
) as response:
    for chunk in response.iter_bytes():
        play_pcm(chunk)  # 24 kHz mono PCM
```

`/generate` nativo con `curl` (campos leídos del código; combinación **no verificado**):

```bash
curl -sS http://127.0.0.1:3900/generate \
  -F text="Hola, bienvenidos al tutorial." -F language=es -F profile_id=<id> \
  -F seed=42 -F num_step=32 -F wav_bits=24 -D headers.txt -o toma.wav
```

CLI **(leída)** `__main__.py`, `docs/install/script.md`:

```bash
voicestudio voices list | cut -f2
voicestudio speak "Hola mundo" --voice "Mi voz" --language es --seed 42 -o hola.wav
voicestudio speak --text-file guion.txt --voice <id> -o guion.wav
voicestudio voices compare <id1> <id2> --text "Prueba de voz" --out-dir comparar/
voicestudio transcribe toma.wav --format srt -o toma.srt
voicestudio --url https://gpu-box:3900 status --json
```

## 5. Tips y Trucos

- Calienta el modelo antes de pedir audio: `GET /models`, `POST /models/install` y esperar `/setup/download-stream`; si no, la primera petición puede agotar el timeout descargando ~2.3 GB. **(leída)** `docs/production-private-api.md`, issue [#1014](https://github.com/debpalash/VoiceStudio/pull/1014).
- `tts-1`/`tts-1-hd` y las voces `alloy`, etc. son alias, no garantías de calidad. Para narración repetible usa un perfil guardado y `seed`. **(leída)** `skills/voicestudio/SKILL.md`.
- Comprueba el estado HTTP y sondea el archivo: un error puede quedar escrito en la ruta de salida. **(leída)** misma fuente.
- Un 429 con `Retry-After` es contrapresión del pool de GPU: respétalo, no reintentes en paralelo. **(leída)** `docs/api-auth.md` §"Status codes".
- `voices compare` genera la misma frase con varias voces: útil para elegir voz de un video. **(leída)** `__main__.py` l. 793-801.
- Un nombre de voz compartido por varios perfiles da 409 `ambiguous_voice`; usa el id. **(leída)** `docs/agentic-voice.md`.
- **conflicto (menor)**: `speed` admite 0.25-4.0 en `/v1/audio/speech` (`openai_compat.py` l. 287-292), pero el docstring de la herramienta MCP `generate_speech` dice 0.5-2.0 (`backend/mcp_server.py`). `/generate` no declara límites en el `Form`.

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#2374](https://github.com/debpalash/VoiceStudio/issues/2374) | cerrado | `/ws/tts` con `engine` creaba un sidecar nuevo por petición (fuga de VRAM, OOM). **(leída)** |
| [#3588](https://github.com/debpalash/VoiceStudio/issues/3588) | cerrado | IndexTTS ignoraba `speed` por API; `/ws/tts` no exponía `duration_factor`. **(leída)** |
| [#1014](https://github.com/debpalash/VoiceStudio/pull/1014) | cerrado | Primera llamada a `/v1/audio/speech` agotaba 300 s descargando el checkpoint; `num_step`/`guidance_scale` se descartaban en `/v1`. **(leída)** |
| [#2679](https://github.com/debpalash/VoiceStudio/issues/2679) | cerrado | Lista de voces vía API OpenAI con formato inesperado para clientes. **(leída)** |
| [#2617](https://github.com/debpalash/VoiceStudio/issues/2617) | cerrado | Pedido de ids de voz legibles en la API OpenAI (hoy se acepta el nombre). **(leída)** |
| [#1585](https://github.com/debpalash/VoiceStudio/issues/1585), [#1651](https://github.com/debpalash/VoiceStudio/issues/1651) | cerrados | 403 "loopback origin (or admin API key) required" en Docker/WSL. **(leída)** #1585; #1651 **(snippet)**. |
| [#3829](https://github.com/debpalash/VoiceStudio/issues/3829) | cerrado | Propuesta que originó el comando `voicestudio`. **(leída)** |

## 7. Qué Dice la Comunidad

- **B** — [computingforgeeks](https://computingforgeeks.com/install-voicestudio/) (2026-10-24, v0.5.6, Docker): usa `/v1/audio/speech` con Bearer. Midió clon por API de 7.6 s de audio: 2.1-2.3 s en RTX 3060 12 GB caliente vs 3 min 58 s en CPU; primer render frío 49.8 s (GPU). Sin `OMNIVOICE_DATA_DIR` se pierden voces al recrear el contenedor; `/health` da 503 mientras arranca.
- **B** — [andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) (sep-2026, updates nov): basta cambiar `base_url`; v0.5.6 añadió `/v1/models`, SSE y MP3 real. Primera síntesis ~42 s en v0.5.1. Advierte que los pesos OmniVoice por defecto son CC-BY-NC aunque la app sea AGPL.
- **B** — [remio.ai](https://www.remio.ai/post/debpalash-voicestudio-hit-github-trending-but-local-voice-ai-still-has-to-prove) (sep-2026): la API compatible facilita integrar, pero los workers remotos amplían la superficie de seguridad.
- **C** — listados como [everydev.ai](https://www.everydev.ai/tools/voicestudio) y [byteiota](https://byteiota.com/voicestudio-local-voice-cloning-openai-api/): repiten el README.

## 8. Qué Sirve para social-videos

Ideas que conviene reimplementar en `narration/tts.py` (sin copiar código AGPL; solo el diseño):

1. **Salida `--json` con códigos de error estables y códigos de salida (0/1/2).** Permite que Claude Code o un script encadenen narración → música → ffmpeg sin parsear texto.
2. **Metadatos de la toma**: devolver/escribir `id`, `duration`, `gen_time`, `seed`, `sample_rate`, y avisar de trozos perdidos (`dropped_chunks`). Un sidecar `.json` junto al WAV en `out/narration/` cumple el mismo papel que las cabeceras `X-Audio-*`.
3. **`--seed` explícito** para reproducir una toma aprobada.
4. **Troceo por oraciones con crossfade configurable** (`max_chunk_chars`, `crossfade_ms`) para guiones largos.
5. **Diccionario de pronunciación con override inline `[[…]]`**, útil para siglas y anglicismos en español neutro.
6. **Comando tipo `voices compare`**: misma frase con varias referencias en una carpeta, para elegir voz.
7. **No hace falta** una API HTTP propia: el CLI local basta para un usuario. Si se quisiera, el contrato `POST /v1/audio/speech` es el estándar de facto que ya entienden n8n, pipecat y el SDK `openai`.
8. Si se usara VoiceStudio como backend (sin copiar código), revisar la licencia del **modelo** elegido: los pesos OmniVoice por defecto son CC-BY-NC según la comunidad (**no verificado** en el repo); para uso comercial preferir motores Apache/MIT.

# Transcripción (Transcriptions / ASR)

> Investigación del 2026-11-15. Motores de voz a texto de VoiceStudio (WhisperX, faster-whisper, Parakeet y otros), cómo se transcribe desde la UI, la API, el CLI y el MCP, los timestamps por palabra y la exportación SRT/VTT para subtítulos. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Clon local consultado: commit `80b4594` (2026-11-16).

---

## 1. Qué Es

* Un registro de motores ASR con selección automática según el hardware, usado por la pestaña **Transcriptions**, el dictado, el doblaje, la transcripción de referencias para clonar y la API compatible con OpenAI **(leída, `docs/engines/README.md` §Speech-to-text, `backend/services/asr_backend.py`)**.
* Orden de autodetección en el código (`asr_backend.py` ~L3285-3300) **(leída)**:
  1. Apple Silicon → `mlx-whisper`.
  2. Windows con HIP → `faster-whisper`; ROCm genérico → `pytorch-whisper`.
  3. Si WhisperX está disponible → **`whisperx`**.
  4. Si no → `faster-whisper`; último recurso → `pytorch-whisper`.
* **Conflicto** menor: el docstring del módulo dice "default: auto-detect, prefers faster-whisper" (`asr_backend.py:21`), pero el código y `docs/engines/whisperx.md` prefieren WhisperX en CUDA y CPU **(leída)**.

| Motor | Para qué | Plataforma | Modelo por defecto | Fuente |
| :--- | :--- | :--- | :--- | :--- |
| **WhisperX** | Doblaje y subtítulos por palabra: faster-whisper + alineación forzada wav2vec2 (±10-30 ms vs ±100-300 ms de Whisper) | CUDA, CPU | `large-v3` (`ASR_MODEL_WHISPERX`) | `docs/engines/whisperx.md` **(leída)** |
| **Faster-Whisper** | Transcripción general, subtítulos donde basta el timing nativo; VAD Silero incluido | CUDA, CPU | `Systran/faster-whisper-large-v3` (`ASR_MODEL_FASTER`) | `docs/engines/faster-whisper.md` **(leída)** |
| Faster-Whisper (isolated) | Lotes desatendidos, aislado de cuelgues | CUDA, CPU | — | `docs/engines/faster-whisper-isolated.md` **(leída)** |
| PyTorch Whisper | Hosts ROCm | CUDA, MPS, CPU | — | `docs/engines/README.md` **(leída)** |
| whisper.cpp | GPUs AMD, CLI nativo | CPU, Vulkan, CUDA, Metal | modelo GGML propio | idem |
| **Parakeet TDT (NeMo)** | 25 idiomas europeos (incluye español), ~6 % WER en inglés, rápido en CPU | CUDA, CPU; **venv separado** | `nvidia/parakeet-tdt-0.6b-v3` (`ASR_MODEL_NEMO`) | `docs/engines/nemo-parakeet.md` **(leída)** |
| Moonshine | Equipos de bajo consumo, **sin timestamps** | CPU | — | `docs/engines/README.md` **(leída)** |
| FunASR (SenseVoice) | 50+ idiomas, diarización en línea | CUDA, CPU | — | idem |
| Sherpa-ONNX | Dictado en streaming | CPU | — | idem |
| Compatible con OpenAI | Endpoint local o remoto configurado | red | — | idem |

---

## 2. Cómo Se Usa

### 2.1 En la UI

* **Transcriptions** (sobre la lista de motores o con la búsqueda de comandos): subir un audio o dictar, y al detener se transcribe. Si no hay modelo activo, ofrece uno instalado o el recomendado tras un clic explícito **(leída, `docs/electron-transcriptions.md`)**.
* Resultados en **History** (máximo 200, el más nuevo primero): buscar, ver tiempos por segmento, copiar, **Save plain text**, **Save SRT** y enviar el texto al guion de clonación **(leída)**.
* **Save SRT** usa los segmentos originales del reconocimiento con sus tiempos reales; si algún segmento no tiene tiempos válidos, SRT no está disponible (Sherpa y Moonshine básico no califican) **(leída)**.
* La transcripción de archivos, MCP/CLI y referencias de clonación **conserva las palabras tal como se dijeron**; la limpieza (muletillas, puntuación hablada) solo aplica al dictado por atajo **(leída, `electron-transcriptions.md`)**.
* Selección de motor: **Model Catalogue → ASR → Use**, o `OMNIVOICE_ASR_BACKEND=<id>`, que manda sobre la UI **(leída, `docs/engines/whisperx.md`)**.

### 2.2 Por API

**Nativa** `POST /transcribe` (`backend/api/routers/capture.py:53`) **(leída)**:

```bash
curl -sS http://localhost:3900/transcribe \
  -F audio=@narracion.wav -F mode=accurate
# → {"text", "segments":[{"start","end","text"}], "language", "duration_s",
#    "transcription_time_s", "engine", "timestamps_available"}
```

* `mode`: `fast` (por defecto; motor de dictado, sin timestamps por palabra), `accurate` (motor ASR activo con timing por palabra) o `reference` (motor activo sin timing por palabra).
* `refine=true`: limpieza opcional con LLM; agrega `refined_text` solo si cambió algo.
* `diarize=true` + `num_speakers` (solo `accurate`): ver [07](07-diarizacion.md).
* **Conflicto**: el campo `language` aparece como "hint" en la herramienta MCP `transcribe`, pero el docstring de `/transcribe` dice "not currently used; auto-detected" y en el código solo se usa como valor de respaldo para el idioma reportado y para pulir el texto; no se pasa al reconocedor (`capture.py` ~L169-230) **(leída)**.
* **Conflicto**: aunque `accurate` calcula palabras, la respuesta de `/transcribe` solo devuelve `start`, `end` y `text` por segmento, sin palabras (`capture.py` ~L392-399) **(leída)**.

**Compatible con OpenAI** `POST /v1/audio/transcriptions` (`backend/api/routers/openai_compat.py:1508`) **(leída)**: la mejor vía para subtítulos.

```bash
# SRT directo
curl -sS http://localhost:3900/v1/audio/transcriptions \
  -F file=@narracion.wav -F model=whisper-1 -F language=es -F response_format=srt > narracion.srt

# Timestamps por palabra (para subtítulos estilo karaoke en reels)
curl -sS http://localhost:3900/v1/audio/transcriptions \
  -F file=@narracion.wav -F model=whisper-1 -F language=es \
  -F response_format=verbose_json -F 'timestamp_granularities[]=word'
```

* `response_format`: `json`, `text`, `verbose_json`, `srt`, `vtt`. Las palabras solo salen con `verbose_json` + `timestamp_granularities=word`.
* Aquí `language` **sí** llega al motor (`options["language"]`), junto con `prompt` (→ `initial_prompt`) y `temperature` (0–1). `stream=true` → 400 (para streaming: WS `/v1/audio/transcriptions/stream`).
* `POST /v1/audio/translations`: transcribe y traduce a inglés (motores Whisper).
* Sin modelo ASR en disco → `409` con el modelo recomendado; **no descarga sola** **(leída)**.

**Doblaje**: `GET /dub/transcribe-stream/{job_id}` (SSE) y `POST /dub/transcribe/{job_id}`; exportación `GET /dub/srt/{job_id}?lang=`, `/dub/vtt/{job_id}` y `/dub/ass/{job_id}` (karaoke) **(leída, `dub_core.py`, `dub_export.py`)**.

### 2.3 Por CLI y MCP

* CLI: `voicestudio dub transcribe <job_id>`, `voicestudio dub transcript get <job_id>`, `voicestudio dictation models|readiness` (`cli/voicestudio_cli/registry.py`) **(leída)**. No vi un comando directo para `/transcribe`; se usa la API **no verificado**.
* MCP: herramienta `transcribe(audio_base64 | audio_path, language)`; `audio_path` debe estar bajo `OMNIVOICE_MCP_BASE_PATH` (sin base configurada, se rechazan las rutas); tope de 200 MB; llama a `/transcribe` en modo `fast` (no envía `mode`) **(leída, `backend/mcp_server.py:1044`)**.

---

## 3. Opciones y Parámetros

| Variable / parámetro | Valor por defecto | Efecto | Fuente |
| :--- | :--- | :--- | :--- |
| `OMNIVOICE_ASR_BACKEND` | autodetección | Fija el motor; gana sobre la UI | `asr_backend.py:3303` **(leída)** |
| `ASR_MODEL_WHISPERX` | `large-v3` | Tamaños `tiny`…`large-v3`, `distil-large-v3` o un repo HF | `whisperx.md` **(leída)** |
| `ASR_MODEL_FASTER` | `Systran/faster-whisper-large-v3` | idem | `faster-whisper.md` **(leída)** |
| `OMNIVOICE_ALIGN_DEVICE` | — | Dispositivo del alineador wav2vec2 | `whisperx.md` **(leída)** |
| `OMNIVOICE_ASR_VRAM_PREFLIGHT` | activo | Antes de cargar compara la VRAM libre: float16 5.0 GB, int8_float16 3.5 GB, int8 3.0 GB; si no alcanza, degrada o pasa a CPU int8. `0` lo desactiva | `whisperx.md` **(leída)** |
| `OMNIVOICE_TRANSCRIBE_CHUNK_TIMEOUT_S` | 120 s | Por trozo del doblaje | `whisperx.md` **(leída)** |
| `OMNIVOICE_ASR_TRANSCRIBE_TIMEOUT_S` | 300 s | Por archivo; como mínimo 2× la duración | idem |
| Alineadores wav2vec2 | ~20 idiomas principales | Fuera de ellos se usan los timestamps nativos de Whisper | `whisperx.md` **(leída)**; que el español esté entre ellos es **(snippet, upstream WhisperX)** |

---

## 4. Ejemplos

* **Subtítulos de una narración generada en español**: `/v1/audio/transcriptions` con `language=es&response_format=srt`; como el texto ya se conoce (el guion), lo útil son los tiempos **(leída para la API; flujo no verificado)**.
* **Subtítulos por palabra para reels**: `verbose_json` + `timestamp_granularities[]=word` con WhisperX activo (alineación forzada) **(leída)**.
* **Video ajeno con subtítulos de YouTube**: en el doblaje, `fetch_subs=true` usa la pista de captions original en vez de Whisper **(leída, `docs/electron-dubbing.md`)**.
* **Exportar solo subtítulos de un video, sin doblar**: tras transcribir en Dubbing, exportar SRT/VTT o un MP4 con subtítulos quemados (línea o karaoke) **(leída, `docs/dubbing/export.md`)**.

---

## 5. Tips y Trucos

* **Para timing fino, WhisperX; para texto, cualquiera**: faster-whisper tiene ±100-300 ms por palabra, WhisperX ±10-30 ms **(leída, `whisperx.md`)**.
* **Parakeet**: devuelve **un solo segmento** para todo el archivo y reporta `en` como idioma aunque detecte otro; malo para subtítulos largos. Nunca instalar NeMo en el venv de la app: rompe `transformers` **(leída, `nemo-parakeet.md`)**.
* **GPU de 8 GB**: cargar large-v3 fp16 con la tarjeta casi llena aborta el proceso entero (CUDA nativo); por eso existe la verificación previa de VRAM. Liberar el TTS antes de transcribir **(leída, `whisperx.md`, [#723](https://github.com/debpalash/VoiceStudio/issues/723), [#255](https://github.com/debpalash/VoiceStudio/issues/255))**.
* **cuDNN 8** es obligatorio para CTranslate2 en CUDA; sin él cae a pytorch-whisper (cuDNN 9) **(leída, [#1371](https://github.com/debpalash/VoiceStudio/issues/1371))**.
* **Cada cue SRT es un segmento ASR completo**: no se cortan por largo de línea (`openai_compat.py` ~L1404-1416) **(leída)**. Para formato vertical hay que re-segmentar a partir de las palabras.
* **Exportaciones**: los tiempos SRT/VTT se redondean una sola vez al milisegundo; VTT escapa el marcado **(leída, `docs/dubbing/translation-engines.md`)**.
* Usar `prompt` (→ `initial_prompt`) con nombres propios o términos técnicos del guion **(leída para el parámetro; efecto no verificado)**.

---

## 6. Problemas Conocidos

| Issue | Qué pasa | Estado |
| :--- | :--- | :--- |
| [#723](https://github.com/debpalash/VoiceStudio/issues/723) | large-v3 fp16 en 8 GB casi llenos tumba el backend sin excepción Python | Mitigado con la verificación de VRAM |
| [#551](https://github.com/debpalash/VoiceStudio/issues/551) | GPUs sin fp16 eficiente (GTX 16xx, Pascal) | Degrada a int8_float16 → int8 |
| [#1371](https://github.com/debpalash/VoiceStudio/issues/1371) | Falta cuDNN 8 → caída inmediata | Se reporta como no disponible |
| [#692](https://github.com/debpalash/VoiceStudio/issues/692) | CTranslate2 ≤ 4.4.0 pide stack ejecutable; kernels endurecidos lo rechazan | Parche automático o `patchelf --clear-execstack` |
| [#730](https://github.com/debpalash/VoiceStudio/issues/730) | Segfault raro al descargar faster-whisper de la GPU | Usar la variante *isolated* |
| [#1185](https://github.com/debpalash/VoiceStudio/issues/1185) | Instalación parcial rompe la cadena whisperx → pyannote → lightning_fabric | `uv sync --reinstall` |
| [#1582](https://github.com/debpalash/VoiceStudio/issues/1582) | WhisperX cae a CPU en AMD ROCm | Cerrado; ROCm usa pytorch-whisper |
| [#4127](https://github.com/debpalash/VoiceStudio/issues/4127) | SRT no se exportaba (v0.3.8) | Cerrado |
| [#1431](https://github.com/debpalash/VoiceStudio/issues/1431) | Tras editar los subtítulos, la exportación salía con el texto viejo | Cerrado |

---

## 7. Qué Dice la Comunidad

* **B**: los issues anteriores muestran fallos de instalación y de VRAM, no de precisión; no encontré quejas sobre la calidad en español **(leída)**.
* **B**: [#1582](https://github.com/debpalash/VoiceStudio/issues/1582) pidió una alternativa a WhisperX para AMD **(snippet, título)**.
* **C**: el benchmark de Parakeet (RTF 0.08-0.23 en CPU de un M2, ~20× más rápido que faster-whisper large-v3 int8) es una medición propia del 2026-07-02 **(leída, `nemo-parakeet.md`)**.
* No hay reseñas independientes de 2025-2026 sobre la transcripción de VoiceStudio **no verificado**.

---

## 8. Qué Sirve para social-videos

| Idea | Cómo aplicarla | Prioridad |
| :--- | :--- | :--- |
| **Subtítulos automáticos de la narración** | `narration/tts.py` ya transcribe con `openai-whisper` (`medium`) para `--evaluar`. Usar `whisperx` (BSD-2, **no verificado**) o `faster-whisper` + alineación para sacar tiempos por palabra y escribir SRT/VTT/ASS con el **texto del guion** (no el del ASR), alineado a los tiempos detectados | Alta |
| **Re-segmentar para vertical** | Cortar cues por largo (p. ej. ≤ 32-42 caracteres, 1-2 líneas) y por pausas, a partir de los tiempos por palabra; VoiceStudio no lo hace en su SRT | Alta |
| **Karaoke por palabra** | Generar `.ass` con `\k` desde los tiempos de WhisperX y quemarlo con ffmpeg (`subtitles=`); idea tomada de `/dub/ass`, reimplementada | Media |
| **Verificación previa de VRAM** | Antes de cargar Whisper, mirar la VRAM libre (`nvidia-smi`) y bajar a `int8_float16`/`int8` o a CPU en lugar de morir; libera el TTS antes (ya se hace con `cargar_qwen.cache_clear()`) | Media |
| **Reportar si los tiempos son reales** | Un flag tipo `timestamps_available` para no exportar SRT con tiempos inventados | Baja |
| **Parakeet** | No: un solo segmento e idioma mal reportado; útil solo para el WER de `--evaluar` en CPU | Baja |

Todo se implementa llamando a las bibliotecas upstream (Whisper, faster-whisper, WhisperX), no copiando código de VoiceStudio (AGPL).

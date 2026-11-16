# Doblaje de Video (Video Dubbing)

> Investigación del 2026-11-15. Cómo funciona el doblaje de VoiceStudio de punta a punta (importar, transcribir, traducir, asignar voces, generar, sincronizar y exportar), el doblaje por lotes y la conversión de voz basada en transcripción. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Clon local consultado: commit `80b4594` (2026-11-16). Rutas relativas a la raíz del repo.

---

## 1. Qué Es

* Un editor de doblaje que recibe audio o video (archivo o URL vía yt-dlp), separa la voz del fondo, transcribe con diarización, traduce, clona la voz de cada hablante y genera la pista doblada en el idioma destino **(leída, `docs/electron-dubbing.md`)**.
* El backend hace todo el trabajo pesado: separación, ASR, clonación, traducción, TTS, ajuste de tiempos, mezcla y exportación. Electron solo edita y orquesta **(leída, `docs/electron-dubbing.md` §"The backend remains responsible…")**.
* El flujo tiene tres pasos visibles en la UI: subir y transcribir, traducir y generar **(leída, `docs/electron-dubbing.md`)**.
* Pipeline interno de ingesta: descarga → extracción de audio → Demucs → detección de escenas → miniatura (`backend/services/dub_pipeline.py`, sección "Ingest pipeline") **(leída)**. Se extraen dos audios: uno de 16 kHz mono para el ASR y otro a calidad completa para la separación, así el fondo no queda "apagado" **(leída, `dub_pipeline.py` ~L1772)**.

---

## 2. Cómo Se Usa

### 2.1 En la UI (paso a paso)

Basado en `docs/dubbing/multi-speaker-guide.md` y `docs/electron-dubbing.md` **(leída)**:

| Paso | Qué hacer | Detalle |
| :--- | :--- | :--- |
| 1. Cargar | **Dubbing** → arrastrar el archivo o pegar un link y pulsar **Ingest** | Bajo el archivo: **Spoken language** (Auto por defecto) y **Speakers** (1–20). Alternativa: **Import .srt** para saltarse el ASR |
| 2. Revisar hablantes | Clic en el nombre del hablante de una fila, o casillas + **Set speaker…** | **New speaker** para un personaje que la diarización no detectó; **Split at cursor** si dos personajes quedaron en una línea |
| 3. Traducir | Elegir idioma destino → **Translate** (o **Translate All** con varios destinos) | Opcional: **Glossary** para nombres y términos; **Paste Translation** para traer una traducción hecha fuera |
| 4. Reparto (Cast) | Cada hablante usa **Auto · Speaker N** (clona su voz del video) o una voz guardada | **Voice match**: *Per line* (por defecto, sigue la entrega de cada línea) o *Consistent* (una referencia por hablante) |
| 5. Generar | **Generate**; escuchar una línea con el botón de auriculares; **Verify** compara tiempos | Al regenerar solo se re-sintetizan las líneas cambiadas |
| 6. Exportar | **Export options** | MP4 con varias pistas, WAV/MP3, SRT/VTT/ASS, subtítulos quemados, karaoke, ZIP de stems/segmentos, TXT |

### 2.2 Por API (FastAPI, puerto por defecto 3900)

Rutas confirmadas en el código **(leída)**:

| Paso | Endpoint | Archivo |
| :--- | :--- | :--- |
| Subir | `POST /dub/upload` (multipart: `video`, `input_type=video\|audio`, `source_lang`) → `202 {job_id, task_id}`; luego SSE `/tasks/stream/{task_id}` hasta el evento `ready` | `backend/api/routers/dub_core.py:838` |
| Importar URL | `POST /dub/ingest-url` (`url`, `source_lang`, `fetch_subs`, `sub_langs`, `cookie_file`) | `backend/schemas/requests.py:285` |
| Transcribir | `GET /dub/transcribe-stream/{job_id}?num_speakers=&per_segment_refs=true` (SSE) o `POST /dub/transcribe/{job_id}?num_speakers=` (síncrono, "legacy para el CLI") | `dub_core.py:1518`, `dub_core.py:2784` |
| Traducir | `POST /dub/translate` con `TranslateRequest` | `backend/api/routers/dub_translate.py:463` |
| Generar | `POST /dub/generate/{job_id}` con `DubRequest` | `backend/api/routers/dub_generate.py:529` |
| Exportar | `GET /dub/download/{job_id}`, `/dub/download-audio`, `/dub/download-mp3`, `/dub/srt`, `/dub/vtt`, `/dub/ass`, `/dub/export-stems`, `/dub/export-segments` | `backend/api/routers/dub_export.py` |
| Lote | `POST /batch/enqueue` (`video`, `langs=es,fr`, `voice_id`, `preserve_bg`, `translation_provider`) | `backend/api/routers/batch.py:815` |

Ejemplo de cuerpo para `POST /dub/translate` (campos de `TranslateRequest`, `backend/schemas/requests.py:159`) **(leída)**:

```json
{
  "job_id": "a1b2c3d4",
  "target_lang": "en",
  "source_lang": "es",
  "provider": "nllb",
  "quality": "autofit",
  "glossary": [{"source": "Destácame", "target": "Destácame"}],
  "segments": [
    {"id": "s1", "text": "Hola, hoy te muestro cómo exportar.", "start": 0.4, "end": 2.9, "slot_seconds": 2.5}
  ]
}
```

Ejemplo de cuerpo para `POST /dub/generate/{job_id}` (campos de `DubRequest`, `requests.py:65`) **(leída)**:

```json
{
  "language": "English",
  "language_code": "en",
  "timing_strategy": "smart_fit",
  "fit_options": {"audio_rate_cap": 1.3, "min_audio_rate": 0.9},
  "voice_match": "consistent",
  "segments": [
    {"start": 0.4, "end": 2.9, "text": "Hi, today I'll show you how to export.",
     "profile_id": "mi-voz", "direction": "friendly, upbeat", "effect_preset": "broadcast"}
  ]
}
```

### 2.3 Por CLI

`cli/voicestudio_cli/registry.py` L233-257 **(leída)** expone: `dub upload`, `dub ingest`, `dub transcribe`, `dub subtitles import`, `dub transcript get|set|clean`, `dub translate`, `dub fit`, `dub generate` (con descarga automática de `/dub/download-audio/{id}`), `dub preview`, `dub tracks`, `dub quality`, `dub cancel`, `dub history`, y `batch enqueue|list|show|cancel|retry|delete|download`. Los archivos se suben como argumento posicional, los cuerpos JSON con `--file`, los campos de formulario con `--field` y los parámetros de query con `--query` (`cli/voicestudio_cli/__main__.py:142-152`) **(leída)**. Ejemplos: `voicestudio dub upload video.mp4`, `voicestudio dub transcribe <job_id> --query num_speakers=2`, `voicestudio dub translate --file traducir.json`, `voicestudio batch enqueue video.mp4 --field langs=en,pt`.

### 2.4 Por MCP

El servidor MCP (`backend/mcp_server.py`) **no tiene herramienta de doblaje**: solo `generate_speech`, `list_voices`, `transcribe`, `clone_voice`, `design_voice`, etc. **(leída)**. El skill `skills/voicestudio/SKILL.md` remite al esquema OpenAPI para el doblaje **(leída)**.

---

## 3. Opciones y Parámetros

### 3.1 Traducción

| Opción | Valores | Nota | Fuente |
| :--- | :--- | :--- | :--- |
| Motor (`provider`) | `argos`, `nllb`, `google`, `deepl`, `microsoft`, `mymemory`, `openai` (LLM compatible OpenAI), agente CLI (Codex, Claude Code, OpenCode, Pi) | Argos y NLLB-200 vienen incluidos y son offline | `docs/dubbing/translation-engines.md` **(leída)** |
| Motor por defecto por API | `TRANSLATE_PROVIDER` o `"google"` si no se manda `provider` | **conflicto**: la doc presenta Argos/NLLB como lo incluido; por API sin `provider` se va a Google (online) | `dub_translate.py:478` **(leída)** |
| `quality` | `fast`, `cinematic`, `autofit`, `agent` | Cinematic y Autofit exigen LLM; sin LLM caen a Fast con aviso | `requests.py:165`, `translation-engines.md` **(leída)** |
| `auto_glossary`, `reflect` | bool (por defecto activos con el LLM) | `reflect` = 3 llamadas LLM por segmento | `translation-engines.md` **(leída)** |
| `condense` | bool (off) | Sugiere una reescritura más corta para segmentos "Won't fit"; nunca la aplica sola | `requests.py` **(leída)** |
| `dialect` | BCP-47 (`es-MX`, `es-AR`, `pt-BR`) | Solo lo aplican los caminos con LLM; NLLB/Argos/Google devuelven `dialect_applied=false` | `requests.py`, `electron-dubbing.md` **(leída)** |
| `translation_instructions` | texto ≤ 5000 caracteres | "Translation style prompt": tono, público, formalidad, modismos | `electron-dubbing.md` §Custom translation style **(leída)** |

### 3.2 Generación y sincronía

| Opción | Valores | Por defecto | Fuente |
| :--- | :--- | :--- | :--- |
| `timing_strategy` | `concise`, `strict_slot`, `smart_fit`, `stretch_video` | API: `concise`. UI: `strict_slot` → **conflicto** entre la API y la UI | `requests.py` (`= "concise"`), `electron/src/shared/store/prefsSlice.ts:320` y `dub-session.ts:212` (`'strict_slot'`) **(leída)** |
| `fit_options` (Smart Fit) | `audio_rate_cap` 1.0–2.0 (1.5), `min_audio_rate` 0.5–1.0 (0.85), `max_audio_only_rate` (1.2), `video_slow_cap` (2.0), `gap_guard_s` (0.05), `allow_video_retime` (true) | valores fuera de rango → 422 | `requests.py` `FitOptions`, `electron-dubbing.md` **(leída)** |
| `voice_match` | `per_line`, `consistent` | `per_line` | `requests.py` **(leída)** |
| `num_step`, `guidance_scale`, `speed` | int / float / float | UI: 16 / 2 / 1 | `electron-dubbing.md` §Production overrides **(leída)** |
| Por segmento | `profile_id`, `instruct`, `direction`, `speed`, `gain` (0–2), `target_lang`, `effect_preset` (`broadcast`…) | — | `requests.py` `DubSegment` **(leída)** |
| `regen_only`, `segment_ids` | lista de ids | regeneración parcial | `requests.py` **(leída)** |
| `preview` | bool | `num_step=8`, ~2× más rápido, ~10-20 % menos calidad | `requests.py` (comentario) **(leída)** |

### 3.3 Exportación (`GET /dub/download/{job_id}`)

| Parámetro | Efecto | Fuente |
| :--- | :--- | :--- |
| `preserve_bg`, `bed_level` (0.0–4.0) | Mezcla el fondo separado bajo el doblaje; limitador contra clipping | `dub_export.py:726`, `docs/dubbing/export.md` **(leída)** |
| `include_tracks`, `default_track` | Pistas de audio en el MP4 (`original,es,en`) y cuál suena por defecto | `dub_export.py` **(leída)** |
| `burn_subs`, `dual`, `karaoke` | Subtítulos quemados; dual = traducción + original en cursiva; karaoke = resaltado por palabra (ASS), incompatible con dual | `dub_export.py`, `export.md` **(leída)** |
| `out_format` | `wav`, `m4a`, `mp3`, `flac` (solo trabajos de audio) | `dub_export.py` **(leída)** |
| `/dub/srt/{id}?lang=&dual=` | SRT de la pista pedida; con Smart Fit o Stretch Video los tiempos salen de la línea de tiempo ajustada | `dub_export.py:2105` **(leída)** |

Codificación de video: libx264 por defecto; "Hardware when available" usa NVENC/QSV/AMF/VideoToolbox y reintenta con libx264 si falla; "Maximum resolution" solo reduce **(leída, `electron-dubbing.md`)**.

---

## 4. Ejemplos

* **Tutorial en español → inglés con la misma voz**: subir el MP4, `Speakers=1`, traducir con `quality=autofit` (LLM local en Ollama), Cast con la voz guardada, `timing_strategy=smart_fit`, exportar MP4 con `include_tracks=original,en`, `default_track=en` y `preserve_bg=1` **(leída, combinación de opciones documentadas; resultado no verificado)**.
* **Video con dos personas** (entrevista, reel conversado): `Speakers=2`, revisar hablantes antes de traducir, `voice_match=consistent` para que no derive la identidad entre líneas **(leída, `multi-speaker-guide.md` §4)**.
* **Solo subtítulos sin doblar**: tras transcribir se puede exportar SRT/VTT o MP4 con subtítulos quemados y el audio original; el editor primero envía las líneas con `POST /dub/sync-transcript/{job_id}` **(leída, `export.md`; issue [#3393](https://github.com/debpalash/VoiceStudio/issues/3393))**.
* **Lote**: `batch enqueue --field langs=en,pt` con `preserve_bg=true`. La cola vive en memoria: si el backend se reinicia, se pierde **(leída, `docs/electron-batch.md`, `batch.py:815`)**.

### 4.1 Conversión de voz basada en transcripción (Tools → Convert)

* **Modo por defecto (transcribir y re-sintetizar)**: transcribe la fuente y sintetiza ese texto con la voz elegida; *Match duration* ajusta solo la duración total (atempo 0.5–2.0×); no conserva el tono, las pausas ni la expresión **(leída, `docs/electron-tools.md`; `backend/api/routers/voice_convert.py:442`)**.
* **Keep my delivery** (#3421): convierte la grabación misma con CosyVoice 3 (no transcribe), conserva el ritmo y la entonación; trozos de ~28 s cortados en pausas; máximo 10 min **(leída, `electron-tools.md`)**.
* **Video voice swap** (#3750): MP4/MOV/M4V/MKV → separa con Demucs, convierte las voces, vuelve a mezclar el fondo y remuxa sin re-codificar la imagen **(leída, `backend/services/video_voice_swap.py`)**.
* API: `POST /convert` (multipart `audio`, `profile_id`, `match_duration`, `language`, `keep_delivery`) **(leída)**.

---

## 5. Tips y Trucos

* **Corregir hablantes antes de traducir**: ahorra un re-doblaje **(leída, `multi-speaker-guide.md` §2)**.
* **Badges *Tight fit* y *Won't fit +Ns***: predicen antes de sintetizar si la línea traducida cabe, sin LLM; acortar el texto antes de gastar GPU **(leída, `translation-engines.md` §Fit prediction)**.
* **Concise y Smart Fit se detienen** si una línea no cabe en vez de cortar palabras: acortar la traducción, usar Strict Slot o permitir Stretch Video **(leída, `electron-dubbing.md` §Speech integrity)**.
* **Mirror source delivery**: escribe en *Direction* palabras como `urgent`, `calm`, `whispered`, `quick` según cómo dijo cada línea el hablante original (volumen, ritmo, tono); nunca infiere emoción. API: `POST /dub/prosody-mirror/{job_id}` **(leída, `electron-dubbing.md`)**.
* **Paste Translation** acepta SRT/VTT con tiempos, líneas numeradas o líneas sueltas; solo marca como "stale" las filas cambiadas para *Regen N changed* **(leída, `translation-engines.md`)**.
* **Captions de YouTube**: con `fetch_subs` se usa la pista de subtítulos original (no las autotraducidas) en lugar de Whisper **(leída, `electron-dubbing.md`)**.
* **Fuera del diálogo** se conserva el audio estéreo original (música, risas, ambiente); dentro, el fondo separado con transiciones de 10 ms **(leída, `electron-dubbing.md` §Preserve sound outside dialogue)**.
* Un personaje con líneas muy cortas puede caer a la voz por defecto: asignarle una voz guardada **(leída, `multi-speaker-guide.md`)**.

---

## 6. Problemas Conocidos

| Issue | Qué pasa | Estado |
| :--- | :--- | :--- |
| [#3419](https://github.com/debpalash/VoiceStudio/issues/3419) | Multi-hablante: turnos fusionados, solo un hablante clonado, deriva de tiempos de varios segundos (sonidos no vocales tomados como inicio) | Cerrado (2026-10); la doc describe el inicio por voz detectada |
| [#4089](https://github.com/debpalash/VoiceStudio/issues/4089) | Voces guardadas con instrucciones de estilo perdían su audio de referencia en el doblaje y cambiaban de identidad entre segmentos | Cerrado, fix #4093 |
| [#1004](https://github.com/debpalash/VoiceStudio/issues/1004) | Doblaje entre idiomas: el TTS leía la frase de referencia en el idioma origen cuando el texto ASR no calzaba con el audio del clip | Cerrado ("Fixed on main") |
| [#3751](https://github.com/debpalash/VoiceStudio/issues/3751) | Demucs falla en fuentes largas (1 h) y no se puede conservar el fondo | Cerrado; se agregó una escalera de reintentos (estándar → `--segment 4 --overlap 0.1` → CPU), `dub_pipeline.py:1547` |
| [#4127](https://github.com/debpalash/VoiceStudio/issues/4127) | SRT no se exportaba (v0.3.8) y pedido de TXT sin tiempos | Cerrado; existe *Save plain text* |
| [#4094](https://github.com/debpalash/VoiceStudio/issues/4094) | Revisión de Discord con reportes de doblaje pendientes | Abierto |

* La propia doc admite que la consistencia de voz en un render multi-hablante real, el efecto audible de `gain` y los exports renderizados por lotes **no están verificados** por sus pruebas **(leída, `electron-dubbing.md`)**.
* No promete lip sync a nivel de fonema **(leída, `electron-dubbing.md`)**.

---

## 7. Qué Dice la Comunidad

* **B**: el issue [#3419](https://github.com/debpalash/VoiceStudio/issues/3419) recoge reportes repetidos de varios usuarios avanzados en Discord (mayo-julio 2026): la queja de doblaje más frecuente era la mezcla de hablantes y la deriva de tiempos **(leída)**.
* **C**: [aiadoptionagency.com](https://aiadoptionagency.com/?p=15649) describe el pipeline (transcribir, traducir, conservar identidad, sintetizar, exportar) sin pruebas propias **(snippet)**.
* No se encontraron reseñas independientes ni comparativas de 2025-2026 que midan la calidad del doblaje en español **no verificado**.

---

## 8. Qué Sirve para social-videos

| Idea | Cómo aplicarla sin copiar código AGPL | Prioridad |
| :--- | :--- | :--- |
| **Doblar un tutorial/reel al inglés con la voz clonada** | Pipeline propio: Whisper → traducción (LLM o NLLB) → `narration/tts.py` con la misma referencia → mezcla con ffmpeg. VoiceStudio confirma el orden de pasos y los puntos críticos | Alta |
| **Predicción de encaje antes de sintetizar** | Estimar segundos por idioma (caracteres o sílabas / tasa medida) y marcar las líneas que no caben; reescribir con el LLM antes de gastar GPU | Alta |
| **Timing "Smart Fit" con topes** | Acelerar el audio con `atempo` solo hasta ~1.2-1.5× y fallar en vez de cortar; nunca recortar palabras | Media |
| **Conservar música fuera del diálogo** | Con Demucs: fondo separado solo dentro de los intervalos hablados y audio original fuera | Media (para videos con música propia, la música ya viene de `music/`) |
| **Voice match "consistent"** | Para narración ya se usa una sola referencia: confirma que es lo correcto para la identidad estable | Ya cubierto |
| **Direcciones por línea** (`urgent`, `calm`…) | Equivalente a los estilos de `narration/` y a la sintaxis del guion | Ya cubierto en parte |

No se recomienda instalar la app: en 8 GB de VRAM WhisperX large-v3 fp16 pide ~5 GB y compite con el TTS (ver [08](08-transcripcion.md)); la regla del repo es un modelo a la vez.

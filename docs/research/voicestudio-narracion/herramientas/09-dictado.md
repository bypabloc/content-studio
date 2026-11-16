# Widget de Dictado y Dictado en Vivo

> Investigación del 2026-11-15. Cubre el widget de dictado con atajo global de VoiceStudio y el dictado en vivo con sherpa-onnx (modelos, inserción, protocolo de streaming para traer tu propio micrófono). Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Fuente principal: clon local del repo `debpalash/VoiceStudio` (commit `80b4594`, 2026-11-16). Rutas relativas a la raíz del repo.

---

## 1. Qué Es

- Dictado de sistema: un atajo global abre una "pill" flotante que graba el micrófono, transcribe localmente y, si el escritorio lo permite, pega el texto en la app donde se pulsó el atajo. La pill nunca toma el foco del teclado. **(leída)** `docs/features/dictation.md`.
- Motor: sherpa-onnx con 7 modelos de dictado. El default es `sherpa-whisper-tiny` (90+ idiomas, autodetección). Parakeet TDT v3 cubre 25 idiomas europeos y no se elige solo. **(leída)** `backend/services/sherpa_dictation.py` (`DEFAULT_MODEL_ID = "sherpa-whisper-tiny"`, l. 234) y `backend/api/routers/dictation.py`.
- Es una herramienta de **entrada** (voz → texto), no de narración. Para social-videos solo interesa de forma indirecta: dictar guiones o transcribir tomas.
- El control nativo del dictado por API (puerto 3902, `/v1/dictation/*`, flags `--dictate-*`) **se retiró** al pasar de Tauri a Electron. Hoy solo el atajo de la app enciende el micrófono. **(leída)** `docs/speech-platform.md` §"Native dictation control is retired".

## 2. Cómo Se Usa

1. Instalar un modelo de dictado desde Model Catalogue y elegirlo en **Settings → Voice** o en el menú Engines (**Transcription → Sherpa-ONNX dictation → Dictation model**). **(leída)** `docs/features/dictation.md`.
2. Configurar el atajo y el modo (`hold` o `toggle`) en **Settings → Hotkey**. Atajo por defecto: `CmdOrCtrl+Shift+Space` **(leída)** `electron/src/shared/utils/dictationShortcut.js` l. 3. Modo por defecto: `toggle` **(leída)** `backend/api/routers/dictation.py` (`_DEFAULT_MODE`).
3. Poner el cursor en un campo de texto, pulsar el atajo, hablar y soltar (hold) o pulsar otra vez (toggle).
4. La pill muestra **Inserted** solo si la inserción nativa funcionó; **Copied** significa que el texto quedó en el portapapeles para pegar a mano. **(leída)** `docs/features/dictation.md`.

Desde la página **Transcriptions** hay un botón **Start dictation** que despierta la ventana grabadora y confirma solo cuando el micrófono arrancó. **(leída)** misma fuente.

### Traer tu propio micrófono (streaming)

Un editor, TUI o script puede capturar audio y enviarlo al backend por WebSocket. **(leída)** `docs/speech-platform.md`; ruta en `backend/api/routers/capture_ws.py` l. 303-304 (`PLATFORM_STREAM_PATH` y `/ws/transcribe`).

```text
ws://127.0.0.1:3900/v1/audio/transcriptions/stream          # WebM/Opus binario por defecto
ws://127.0.0.1:3900/v1/audio/transcriptions/stream?pcm=1&sr=16000   # PCM s16le mono
```

Para cerrar el turno sin cerrar el socket: `{"type":"input_audio.end"}`. Respuestas:

```json
{"type":"session.started","protocol":"voicestudio.speech.v1","session_id":"..."}
{"type":"partial","text":"hello wor...","session_id":"..."}
{"type":"final","final_kind":"summary","text":"Hello world.","session_id":"..."}
```

Los modelos sherpa de streaming pueden emitir antes `final_kind: "utterance"`. **(leída)** `docs/speech-platform.md`.

## 3. Opciones y Parámetros

| Opción | Valores | Fuente |
| :--- | :--- | :--- |
| Modelo (`dictation.model_id`) | `sherpa-whisper-tiny` (default), `sherpa-parakeet-tdt-v3`, `sherpa-parakeet-tdt-v2` (inglés), `sherpa-zipformer-bilingual-zh-en`, `sherpa-paraformer-bilingual-zh-en`, `sherpa-zipformer-en-20m`, `sherpa-zipformer-zh-14m` | `backend/services/sherpa_dictation.py` **(leída)** |
| Modo (`dictation.mode`) | `toggle` (default), `hold` | `backend/api/routers/dictation.py` **(leída)** |
| Pista de vocabulario (`dictation.prompt`) | texto ≤ 1000 caracteres (nombres, jerga, grafías); solo lo usan motores tipo Whisper | `backend/api/routers/dictation.py` docstring **(leída)** |
| Atajo | `CmdOrCtrl+Shift+Space` por defecto | `electron/src/shared/utils/dictationShortcut.js` **(leída)** |
| `VOICESTUDIO_WAYLAND_UNTARGETED_INSERT=1` | Inserta en la ventana con foco al terminar (Wayland); usa `wtype`, `dotool` o `ydotool` | `docs/features/dictation.md` **(leída)** |
| Endpoints REST | `GET /dictation/models`, `GET /dictation/readiness`, `GET/POST /dictation/prefs` (solo loopback, `require_local`) | `backend/api/routers/dictation.py` l. 82-142 **(leída)** |
| CLI | `voicestudio dictation models`, `dictation readiness`, `dictation preferences show/set` | `cli/voicestudio_cli/contracts.json` **(leída)** |

Inserción por plataforma **(leída)** `docs/features/dictation.md`:

| Plataforma | Comportamiento |
| :--- | :--- |
| macOS | Reactiva la app capturada y envía Cmd-V. Sin permiso de Accesibilidad queda copiado. |
| Windows | Valida ventana y proceso, pide foco y envía Ctrl-V. Si Windows niega el foco, queda copiado. |
| Linux X11 | Reactiva la ventana vía EWMH y envía Ctrl-V. |
| Wayland | Solo copia (no hay identidad portable de ventana). |
| Modo navegador | Solo copia. |

## 4. Ejemplos

Ver capacidades y transcribir un archivo con el cliente sin dependencias (requiere checkout del repo) **(leída)** `docs/speech-platform.md`:

```bash
curl http://127.0.0.1:3900/.well-known/voicestudio-speech
python -m backend.speech_client capabilities
python -m backend.speech_client transcribe recording.wav
```

Cambiar el modelo y la pista de vocabulario desde la terminal (forma genérica `--field` de los comandos del registro) **(leída)** `cli/voicestudio_cli/__main__.py` l. 151 y `contracts.json`; combinación concreta **no verificado**:

```bash
voicestudio dictation preferences set --field model_id=sherpa-whisper-tiny \
  --field prompt="Qwen3-TTS, Chatterbox, ACE-Step, social-videos"
```

## 5. Tips y Trucos

- Usa `dictation.prompt` para nombres propios y siglas (ej.: nombres de modelos o del canal). Se lee en cada transcripción y no recarga el motor. **(leída)** `backend/api/routers/dictation.py`.
- Si un modelo devuelve vacío, VoiceStudio reintenta con otro ASR **ya instalado** y degrada el modelo "mudo"; nunca descarga nada solo. **(leída)** `docs/features/dictation.md`.
- La pill tiene **Pause/Resume**, **Stop** y **Close**. Pause congela el temporizador y no se activa por silencio. **(leída)** misma fuente.
- El portapapeles se respalda (texto, HTML, imagen, lista de archivos) y se restaura después del pegado; si copias algo durante la transcripción, no se pisa. **(leída)** misma fuente.
- Para español, Whisper Tiny es el único modelo de la lista que lo cubre además de Parakeet v3 (europeo). La calidad de Whisper Tiny en español latino no está medida en el repo. **no verificado**.

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#3154](https://github.com/debpalash/VoiceStudio/issues/3154) | cerrado | Las pausas insertaban rachas de espacios (finales vacíos confirmados) con Parakeet v3, modo hold, Windows. **(leída)** |
| [#3879](https://github.com/debpalash/VoiceStudio/issues/3879) | cerrado | En Snap, el helper nativo necesitaba GLIBC 2.38+ y el atajo de dictado no se registraba. **(leída)** |
| [#1333](https://github.com/debpalash/VoiceStudio/issues/1333) | cerrado | AppImage en Linux no enumeraba micrófonos. **(snippet)** solo título. |
| [#3878](https://github.com/debpalash/VoiceStudio/issues/3878) | cerrado | Snap 0.5.7 segfault en Wayland nativo (GNOME 50); funciona con `--ozone-platform=x11`. **(snippet)** solo título. |

- Wayland: sin inserción automática por defecto; es una limitación de diseño, no un bug. **(leída)** `docs/features/dictation.md`.
- **conflicto**: la reseña de andrew.ooo (sep-2026, actualizada nov-2026) describe "un sidecar de control en Rust" para que agentes y VS Code activen el dictado. El repo actual dice que ese control (puerto 3902) está retirado en Electron. Vale el repo. `docs/speech-platform.md`.

## 7. Qué Dice la Comunidad

- **B** — [andrew.ooo, reseña](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) (2026-09-08, con updates oct/nov): widget con atajo global, transcripción en vivo y limpieza opcional con LLM local. Parte de su descripción del control externo quedó obsoleta (ver **conflicto** arriba).
- **B** — [remio.ai](https://www.remio.ai/post/debpalash-voicestudio-hit-github-trending-but-local-voice-ai-still-has-to-prove) (sep-2026): el dictado "depende de baja latencia"; el proyecto es beta activa.
- **B** — [computingforgeeks](https://computingforgeeks.com/install-voicestudio/) (2026-10-24, v0.5.6): el dictado es un paso opcional del asistente que necesita un modelo STT aparte; no lo probó.
- No encontré mediciones independientes de latencia o WER del dictado. **no verificado**.

## 8. Qué Sirve para social-videos

- **No conviene copiar** el widget: `narration/tts.py` genera audio, no lo captura. El dictado global de VoiceStudio (o cualquier dictador del SO) puede usarse tal cual para dictar borradores de guion.
- **Idea útil (sin código AGPL):** la "pista de vocabulario" (`prompt` ≤ 1000 caracteres). Si en el futuro se añade una verificación ASR de las tomas (comparar texto pedido vs. texto oído, como en la evaluación de narración), pasar a Whisper un `initial_prompt` con nombres propios del guion reduce falsos errores. Implementable con `faster-whisper` (MIT) directamente.
- **Idea útil:** el protocolo `partial`/`final` con `session_id` es un buen contrato si algún día se quiere previsualizar una transcripción en vivo; hoy no hace falta.

# VoiceStudio: Qué Es y Qué Se Toma de Él

> Investigación del 2026-11-15. Qué es [debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio), qué motores envuelve y por qué en este repo se integran los motores directamente y no la app. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto** ([01](01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

* App de escritorio, móvil y servidor para voz local: clonación, diseño de voz, doblaje de video, dictado, transcripción y audiolibros. Licencia **AGPL-3.0** **(leída, README)**.
* Stack: Electron + frontend web + backend Python (FastAPI) con motores en procesos separados (*sidecars*), cada uno con su venv. Tiene API local (`POST /generate`, `/ws/tts`), servidor MCP y CLI **(leída, `docs/`, `backend/`)**.
* **No es un modelo**: es un orquestador de más de 20 motores TTS y ASR. Su motor por defecto es **OmniVoice** (k2-fsa) **(leída, `docs/engines/README.md`)**.
* Versión comercial cerrada (VoiceStudio Pro) y nube "próximamente"; el escritorio sigue gratis **(leída, README)**.

---

## 2. Motores TTS que Envuelve (los que hablan español o inglés)

| Motor | Clonación | Control expresivo | Licencia de pesos | En esta investigación |
| :--- | :--- | :--- | :--- | :--- |
| **OmniVoice** (default) | Sí | 13 etiquetas no verbales, `instruct` de diseño cerrado, `speed` | **CC-BY-NC** + tokenizer Higgs | Sí: [03](03-omnivoice.md) |
| **VoxCPM2** | Sí + diseño | Instrucción libre `(…)` al inicio del texto | Apache-2.0 | Sí: [04](04-voxcpm2.md) |
| **IndexTTS 2.5** | Sí | Vector de 8 emociones, `emo_text`, clip de emoción | bilibili Model Use License | Sí: [05](05-indextts-2-5.md) |
| **CosyVoice 3** | Sí | `[breath]`, `<strong>`, instrucción con `<\|endofprompt\|>` | Apache-2.0 (con *disclaimer* académico) | Sí: [06](06-cosyvoice-3.md) |
| Qwen3-TTS Base (adaptador CUDA) | Sí | Ninguno | Apache-2.0 | Ya está en `narration/` |
| MOSS-TTS, dots.tts, Ming, Confucius4, PocketTTS, Supertonic, KittenTTS, GPT-SoVITS, audio.cpp… | Varía | Varía | Varía | Fuera de alcance (acordado con el usuario) |

Fuente: `docs/engines/README.md`, `docs/expressive-speech.md`, `docs/licensing/model-license-data.json` del clon local **(leída)**.

---

## 3. Lo que VoiceStudio Aporta como Conocimiento

Aunque no se use la app, su documentación es la fuente práctica más completa sobre estos motores. Lo más útil:

| Tema | Lo que dice | Dónde |
| :--- | :--- | :--- |
| **La referencia es dirección de actuación** | "Zero-shot cloning mirrors the *delivery* of the reference, not just the timbre — a flat reference clones flat"; es "the most reliable expressive control in the app" | `expressive-speech.md` **(leída)** |
| **Etiquetas desconocidas se leen** | "unrecognized tags are not stripped… Pasting an ElevenLabs script full of `[excited]` / `[whispers]` degrades output on every engine we ship" | `expressive-speech.md` **(leída)** |
| Pausas | `[pause 500ms]` se implementa **fuera del modelo**, pegando silencio real; igual que `[pausa N]` de `tts.py` | `expressive-speech.md` **(leída)** |
| Uniones | Cada motor deja su propio silencio en los bordes; recomiendan recortar a −40 dBFS y poner gaps explícitos (~250 ms entre líneas, ~350 ms entre párrafos) | `expressive-speech.md` **(leída)** |
| Respiración a demanda | Solo CosyVoice 3 (`[breath]`). En OmniVoice: grabarla en la referencia, escribir fragmentos cortos con pausas, `postprocess_output=False`, `class_temperature` 0.3–0.7 y generar varias tomas | `expressive-speech.md` **(leída)** |
| Emoción por línea | `[emotion:TEXTO]` en audiolibros: se traduce a `emo_text` (IndexTTS) o a la instrucción (CosyVoice, VoxCPM2). Un cambio de emoción dentro de una oración rompe la entonación: **una emoción por oración o párrafo** | `expressive-speech.md` **(leída)** |
| Largo de la referencia | Recomienda 5–15 s. OmniVoice usa hasta 20 s; VoxCPM2 los primeros 30 s | `engines/README.md` §Reference clip length **(leída)** |
| Licencias | OmniVoice registrado como `noncommercial`; VoxCPM2 `commercial` sin revisar; IndexTTS fuera de su declaración comercial | `licensing/model-license-data.json` **(leída)** |
| Validación | Escaneo de silencios, clipping y saltos de volumen; Whisper large-v3 para inteligibilidad | `audio-quality.md` **(leída)** |

---

## 4. Por Qué Motores Directos y No la App

Decisión del usuario del 2026-11-15 ([README](README.md#decisiones-tomadas)): **agregar los motores como `--modelo` de `narration/tts.py`**, cada uno en su venv.

| Opción | A favor | En contra |
| :--- | :--- | :--- |
| **Motores directos** (elegida) | Mismo patrón que Qwen y Chatterbox; reutiliza `--evaluar`, `--reintentos`, estilos y pausas; sin depender de Electron ni de un servidor; el código propio no hereda la AGPL | Hay que mantener cuatro venvs y resolver la instalación de cada motor |
| Cliente de la API de VoiceStudio | Todos los motores y su normalización ya resueltos | Depende de la app corriendo; AGPL para modificaciones de la app; capa extra entre `tts.py` y el modelo |

La AGPL de VoiceStudio **no aplica** a este repo mientras no se copie su código: solo se usaron sus documentos como fuente y se importan los paquetes upstream de cada motor (licencias propias, ver [07](07-comparativa-y-licencias.md)).

---

## 5. Recepción

* El repo muestra ~111k estrellas y ~12k forks **(leída, página de GitHub)**. Una cifra tan alta para un proyecto de 2026 no se pudo contrastar con discusiones de comunidad: **no verificado** que refleje uso real.
* La comunidad discute los **motores**, no la app: ver [12](12-recepcion-de-la-comunidad.md).

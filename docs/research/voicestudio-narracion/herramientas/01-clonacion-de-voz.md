# Clonación de Voz

> Investigación del 2026-11-15. Cubre el workspace **Clone** (Voice Cloning) de VoiceStudio: referencia, transcripción, perfiles, bloqueo de identidad, calidad de audio, controles de voz, emoción, etiquetas, pronunciación, Check audio e historial. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

Rutas relativas al repo `debpalash/VoiceStudio` (clon local, licencia AGPL-3.0, último push 2026-11-16 según `gh api`).

---

## 1. Qué Es

- Clonación **zero-shot**: un clip de referencia corto condiciona al modelo; no hay entrenamiento. El motor por defecto es OmniVoice (24 kHz mono). **(leída)** `docs/engines/omnivoice.md`, `docs/audio-quality.md`.
- La referencia no solo transfiere el timbre: también la **acústica** (un cuarto con eco clona con eco) y la **entrega** (una referencia plana clona plana). Según la doc, es "el control expresivo más confiable de la app". **(leída)** `docs/generation-parameters.md` (tip "reference-clip quality transfers"), `docs/expressive-speech.md` §"Every engine".
- Cada voz se guarda como **perfil** (`kind=clone` o `kind=design`) con nombre, retrato, transcripción, idioma, estilo y una semilla opcional. **(leída)** `backend/api/routers/profiles.py` (`POST /profiles`).

---

## 2. Cómo Se Usa

### 2.1 En la UI (Electron)

1. **Referencia**: subir un archivo o grabar. Para grabar se elige el micrófono y el modo Auto, Mono o Stéreo en el panel Voice. Un medidor de entrada confirma la señal y nunca reproduce el micrófono por los altavoces. **(leída)** `docs/generation-parameters.md`.
2. **Guardar perfil**: tras subir o grabar aparece un formulario con nombre y retrato. **Use without saving** usa la referencia temporal. **Change voice** abre el selector sin perder el guion. **(leída)** `docs/profile-portraits.md`.
3. **Transcripción automática**: la referencia nueva pasa por el pipeline local de dictado (Parakeet o Whisper). Si no hay modelo instalado, se escribe la transcripción a mano o se instala uno con un clic. El ASR nunca sobrescribe texto editado mientras corre. **(leída)** `docs/profile-portraits.md` §"Reference transcription and editing".
4. **Guion**: escribir, pegar o importar (TXT, Markdown, DOC, DOCX, PDF, EPUB; sin OCR). **Insert** abre el selector de etiquetas expresivas junto al cursor. **(leída)** `docs/profile-portraits.md`.
5. **Ajustes**: **Audio quality** (formato WAV, refinamiento, nivelado), **Voice controls** (velocidad, duración, limpieza y **Advanced model tuning**) y **Emotion** (corazón, junto a Synthesize). **(leída)** `docs/audio-quality.md`, `electron/src/renderer/src/features/clone/action-bar.tsx`.
6. **Synthesize**: el take aparece en el reproductor fijo inferior y en **Recent takes** (historial). Bajo el take está **Check audio**. **(leída)** `docs/audio-quality.md`, i18n `clone.history_title`.
7. **Lock voice identity**: desde el historial se fija la voz a un take concreto (referencia + semilla), con lo que la voz se vuelve reproducible bit a bit. **(leída)** `docs/expressive-speech.md` (seed), i18n `sidebar.lock_identity`, `POST /profiles/{id}/lock`.

### 2.2 API REST

Crear perfil clonado (multipart), según `backend/api/routers/profiles.py:126`:

```bash
curl -X POST http://127.0.0.1:3900/profiles \
  -F name="Narrador ES" -F kind=clone -F language=Spanish \
  -F ref_audio=@ref.wav -F ref_text="Texto exacto que dice el clip."
```

Generar (`POST /generate`, multipart, `backend/api/routers/generation.py:1902`):

```bash
curl -X POST http://127.0.0.1:3900/generate \
  -F text="Hoy te muestro tres atajos para editar más rápido. [pause 0.5s] Empecemos." \
  -F profile_id=<id> -F language=Spanish -F seed=1234 \
  -F num_step=32 -F speed=1.0 -F wav_bits=24 -F effect_preset=broadcast \
  -o take.wav
```

Bloquear identidad a un take del historial (`profiles.py:1132`, form `history_id`, `seed` opcional):

```bash
curl -X POST http://127.0.0.1:3900/profiles/<id>/lock -F history_id=<take_id> -F seed=1234
```

El puerto 3900 sale del issue [#2970](https://github.com/debpalash/VoiceStudio/issues/2970) ("not responding on port 3900"). **(snippet)**

### 2.3 CLI `voicestudio`

Comandos en `cli/voicestudio_cli/__main__.py` (líneas 165-200 y 718-813) y `registry.py`. **(leída)**

```bash
voicestudio voices clone --name "Narrador ES" --audio ref.wav --ref-text "..." --language Spanish
voicestudio speak "Texto del reel" --voice "Narrador ES" --language Spanish --seed 1234 --output out.wav
voicestudio speak --text-file guion.txt --voice <id> --speed 1.1 --output out.wav
voicestudio voices compare <id1> <id2> --text "Frase de prueba" --out-dir ./cmp   # misma frase, varias voces
voicestudio voices lock <id> --file lock.json      # {"history_id": "...", "seed": 1234}
```

`speak` solo envía `text`, `profile_id`, `speed`, `engine`, `language`, `seed` e `instruct`. Para `num_step`, `wav_bits` o emoción hay que llamar a `/generate` directamente. **(leída)** `__main__.py:792-813`.

### 2.4 MCP

Herramientas `clone_voice` (audio en base64 o `ref_audio_path` dentro de `OMNIVOICE_MCP_BASE_PATH`) y `generate_speech` (WAV por defecto, `format="ogg"`/`"opus"` con ffmpeg). **(leída)** `docs/mcp.md` líneas 13-41.

---

## 3. Opciones y Parámetros

### 3.1 Referencia

| Aspecto | Valor | Fuente |
| :--- | :--- | :--- |
| Duración recomendada (UI) | "Use 5–15 seconds of clean speech" | i18n `clone.reference_hint` **(leída)** |
| Duración óptima OmniVoice | 3–10 s ("sweet spot") | `docs/engines/omnivoice.md` **(leída)** |
| Máximo con transcripción | 20 s (`max_ref_seconds = 20.0`) | `backend/services/tts_backend.py:1900` **(leída)** |
| Sin transcripción | Busca hasta 75 s en 5 pasadas ASR y usa la ventana de 15 s con más habla | `docs/engines/omnivoice.md` **(leída)** |
| Clip > 20 s con `ref_text` en la petición | Error 400 `[clone_ref_too_long]` | `generation.py:2255-2277` **(leída)** |
| VoxCPM2 | Hasta 30 s | `backend/engines/voxcpm2_subprocess/__init__.py:57` **(leída)** |
| Formatos (reemplazo de referencia) | WAV, MP3, M4A, FLAC, OGG, Opus, AAC, WebM; hasta 128 MiB | `docs/profile-portraits.md` **(leída)** |
| Clips silenciosos | Recorte de silencio adaptativo; solo rechaza audio vacío | `docs/generation-parameters.md` **(leída)** |

**Conflicto** de recomendación: la UI dice 5–15 s, la doc del motor dice 3–10 s y el issue [#2281](https://github.com/debpalash/VoiceStudio/issues/2281) pidió aceptar clips más largos (cerrado; de ahí sale la ventana de 15 s sobre 75 s).

### 3.2 Audio quality

| Control | Valores | Por defecto | Fuente |
| :--- | :--- | :--- | :--- |
| WAV (`wav_bits`) | Standard 16-bit (2,9 MB/min), For editing 24-bit (4,3 MB/min), Original 32-bit float (5,8 MB/min) | 16 | `docs/audio-quality.md` **(leída)** |
| Voice refinement (`num_step`) | OmniVoice, VoxCPM2 y dots.tts: 8–64; Supertonic-3: 5–12 | 32 (12 en Supertonic) | `docs/audio-quality.md` **(leída)** |
| Even out volume (`effect_preset`) | `broadcast` (highpass 80 Hz, leveler -20 dB, EQ, limitador -1 dBFS), `cinematic`, `podcast`, `raw`, `warm`, `bright` | `broadcast` | `backend/services/audio_dsp.py:62` **(leída)** |

**Conflicto**: si `num_step` no se envía, `/generate` toma `tts_defaults(engine)` y como último recurso usa 16 (`generation.py`, `sampling_defaults.get("num_step", 16)`). La doc afirma que el valor por defecto es 32 ("best quality"). Por la UI llega 32; por API depende del perfil de rendimiento. **(leída)**

**Sugerencia de ajustes más rápidos**: cuando la estimación es de 45 s o más (o de 15 s o más y 3 veces la duración del audio), la app propone bajar el refinamiento a la mitad (32 → 16 → 8). Las mediciones se guardan solo en el equipo. **(leída)** `docs/audio-quality.md`.

### 3.3 Voice controls y Advanced model tuning

Mapeo de etiquetas de la UI a parámetros de `/generate`, sacado de `features/clone/action-bar.tsx:72-125` y `en.json`: **(leída)**

| Etiqueta UI | Parámetro | Rango UI | Defecto modelo |
| :--- | :--- | :--- | :--- |
| Speed | `speed` | 0,5–2,0 × | 1,0 |
| Duration (s) | `duration` (tiene prioridad sobre `speed`) | vacío = natural | None |
| Prompt guidance | `guidance_scale` | 1–4 | 2,0 |
| Refinement timing | `t_shift` | 0–1 | 0,1 |
| Sampling order variation | `position_temperature` | 0–10 | 5,0 |
| Sound variation | `class_temperature` | 0–2 | 0,0 (codicioso) |
| Coarse-to-fine balance | `layer_penalty_factor` | 0–10 | 5,0 |
| Clean reference noise | `denoise` | on/off | on |
| Polish generated audio | `postprocess_output` (quita silencios largos) | on/off | on |

Defectos del modelo: `docs/generation-parameters.md`. **Conflicto** menor: la UI llama a `denoise` "Clean reference noise", pero la doc lo define como el token `<|denoise|>` que pide al modelo una salida más limpia, no como una limpieza de la referencia. La limpieza de la referencia es `preprocess_prompt`.

Textos largos: `/generate` parte el texto en frases si supera `max_chunk_chars` (800 por defecto) y une los trozos con `crossfade_ms` (50 por defecto). **(leída)** `generation.py:1945-1948`.

### 3.4 Emotion (por motor)

| Motor | Tipo (`expression_caps.emotion`) | Cómo | Fuente |
| :--- | :--- | :--- | :--- |
| OmniVoice (defecto) | `none` | Solo etiquetas no verbales y el estilo `whisper` | `docs/expressive-speech.md` **(leída)** |
| IndexTTS2 | `graded` | **Description** (`emo_text` con intensidad `emo_alpha` 0–0,6 en la UI) o **Sliders** (`emo_vector` con 8 valores 0–1: happy, angry, sad, afraid, disgusted, melancholic, surprised, calm) | ídem; `generation.py` (`emo_alpha` le=1.0) **(leída)** |
| CosyVoice 3 | `direction` | **Delivery direction** → `instruct` en lenguaje natural | ídem **(leída)** |
| VoxCPM2 | `direction` | `instruct`, mapeado al prefijo `(speaking fast, out of breath) ...` | ídem **(leída)** |

Mezclar `emo_text` y `emo_vector`, o mandar intensidad sin texto, devuelve 422 antes de cargar el modelo. **(leída)**

### 3.5 Etiquetas (Insert) y pausas

| Etiqueta | Motor | Nota |
| :--- | :--- | :--- |
| `[pause]` (350 ms), `[pause 500ms]`, `[pause 1.5s]` | Todos | Máximo 10 s; las pausas consecutivas se suman. Regex en `omnivoice/utils/text.py:250` **(leída)** |
| `[laughter]`, `[sigh]` y 11 interjecciones (`[question-ah]`, `[surprise-wa]`, …) | OmniVoice | La mayoría están afinadas para mandarín **(leída)** |
| `[breath]`, `<strong>…</strong>` | CosyVoice 3 | Opt-in **(leída)** |

Las etiquetas desconocidas **no se eliminan**: el motor las lee en voz alta. Insert desactiva las que el motor activo no renderiza. **(leída)** `docs/expressive-speech.md`.

### 3.6 Pronunciación

- Inline: `[[Nuh-VAD-uh]]` siempre gana sobre el diccionario. **(leída)**
- Diccionario con alcances: global → idioma → voz → voz+idioma (gana el más específico). Coincidencia literal sin distinguir mayúsculas; el término más largo gana. **(leída)** `docs/expressive-speech.md`.
- API: `GET/POST /pronunciation`, `/pronunciation/test`, `/pronunciation/export|import` con `profile_id` opcional. `pronounce=false` en `/generate` desactiva el diccionario para esa petición. **(leída)** `backend/api/routers/pronunciation.py`.

---

## 4. Ejemplos

**Guion de tutorial (OmniVoice, español neutro):**

```text
Abre el panel de capas. [pause 0.4s] Ahora, con la tecla Alt presionada, arrastra la capa hacia abajo.
¿Listo? [pause 0.3s] Así de fácil se duplica.
```

**Reel con risa breve (OmniVoice):**

```text
Probé editar un video entero solo con atajos... [laughter] y sí, funcionó.
```

**Dirección de entrega (CosyVoice 3 o VoxCPM2, campo Delivery direction):**

```text
instruct = "tono cálido y entusiasta, ritmo ágil, como presentando un producto"
```

**Respiración "a demanda" en OmniVoice (receta documentada, no es una función):** **(leída)** `docs/expressive-speech.md` §"Breaths"

1. Referencia de 8–15 s con respiraciones audibles.
2. Texto fragmentado: `No puedo… [pause 300ms] no puedo seguir… [pause 200ms] seguir corriendo.`
3. `postprocess_output=false`.
4. `class_temperature` entre 0,3 y 0,7 y varios takes.
5. Bloquear el take ganador (lock con semilla).

**Pronunciación de marcas:** `Descarga [[cap-cut]] y ábrelo.` o una entrada de diccionario `CapCut → cap cut` con alcance "This voice".

---

## 5. Tips y Trucos

- Grabar la referencia **seca y con el micrófono cerca**: el eco del cuarto se clona. **(leída)** `docs/generation-parameters.md`.
- La **entrega** de la referencia es la entrega del clon. Conviene tener una referencia por registro: "tutorial calmado", "reel enérgico". **(leída)** `docs/expressive-speech.md`.
- Clonación entre idiomas: la transcripción va en el idioma del clip y el guion en el idioma de salida. El selector de idioma no traduce. **(leída)** `docs/engines/omnivoice.md`.
- `language=Auto` explícito anula el idioma guardado en el perfil; omitirlo conserva el del perfil. **(leída)** ídem.
- Semilla sin fijar = cada take distinto. Para variantes A/B de un reel se generan varios takes y se bloquea el mejor. **(leída)** `docs/expressive-speech.md`.
- La puntuación (puntos suspensivos, guiones, exclamaciones) cambia el ritmo de verdad y no cuesta nada. **(leída)** ídem.
- 24-bit solo si se va a editar o masterizar después. La precisión de exportación no recupera detalle que el motor ya descartó. **(leída)** `docs/audio-quality.md`.
- Check audio detecta silencios largos, cambios de volumen, clipping, audio vacío y muestras inválidas (hasta 2 h y 100 avisos). No mide parecido ni naturalidad. **(leída)** ídem.
- Reemplazar la referencia de un perfil borra su take bloqueado y su verificación de voz propia, e invalida las cachés. **(leída)** `docs/profile-portraits.md`.

---

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#3730](https://github.com/debpalash/VoiceStudio/issues/3730) | Cerrado | En guiones largos de `/generate` la semilla avanzaba por trozo (`seed + i`) y cambiaba la voz diseñada a mitad del take **(leída)** |
| [#1739](https://github.com/debpalash/VoiceStudio/issues/1739) | Cerrado | El fonema final de cada frase se fragmentaba en micro-ráfagas ("phoneme confetti"), determinista por semilla **(leída)** |
| [#4065](https://github.com/debpalash/VoiceStudio/issues/4065) | Cerrado (2026-11-13) | Clone no encolaba takes: un segundo Synthesize se descartaba. Se pidió una cola **(leída)**. Que la cola esté implementada **no verificado** |
| [#4199](https://github.com/debpalash/VoiceStudio/issues/4199) | Abierto | CosyVoice 3 con referencia añade u omite frases (semillas 42, 43 y 44) **(leída)** |
| [#2093](https://github.com/debpalash/VoiceStudio/issues/2093) | Cerrado | `instruct` de VoxCPM2 ignorado en v0.5.2 **(leída)** |
| [#2535](https://github.com/debpalash/VoiceStudio/issues/2535) | Cerrado | Re-bloquear una voz reproducía audio cacheado del take anterior **(leída)** |
| [#2201](https://github.com/debpalash/VoiceStudio/issues/2201) | Cerrado | 400: el motor `mlx-audio` no soporta clonación **(snippet)** |
| [#315](https://github.com/debpalash/VoiceStudio/issues/315) | — | En Windows, los takes posteriores al primero salían con estática (citado por la reseña de andrew.ooo) **(snippet, no verificado)** |

---

## 7. Qué Dice la Comunidad

- **B**: [andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) (2026-09-08, actualizado 2026-10-15) se basa sobre todo en docs y release notes. Recomienda 5–15 s de un solo hablante y cita a un usuario de Reddit: OmniVoice "way better than Qwen3, Chatterbox". Advierte que los **pesos de OmniVoice son CC-BY-NC** (no comerciales). Esto coincide con el repo: `docs/model-credits.md` habla de "Apache-2.0 code from CC-BY-NC weights". **(leída)**
- **A**: el issue [#3422](https://github.com/debpalash/VoiceStudio/issues/3422) recoge más de 6 pedidos en Discord: "monotone, no emotion" y "make the clone scared in parts and excited in others". De ahí salieron el botón Emotion y las etiquetas grises. **(leída)**
- **C**: listados como everydev.ai y besthub.dev solo repiten el README. **(snippet)**

---

## 8. Qué Sirve para social-videos

Ideas para `narration/tts.py`, reimplementadas sin copiar código AGPL:

1. **Gramática `[pause]`** idéntica: `[pause]` = 350 ms, `[pause 500ms]`, `[pause 0.5s]`, máximo 10 s, pausas adyacentes sumadas y silencio real insertado entre trozos sintetizados. Funciona igual con cualquier motor (Qwen3-TTS o Chatterbox).
2. **Relleno con room tone** (opcional): rellenar las pausas con ruido modelado sobre el piso del propio take, con fundido de 40 ms, en vez de ceros digitales ([#3611](https://github.com/debpalash/VoiceStudio/issues/3611)).
3. **Validación de etiquetas por motor**: avisar o fallar si el guion trae una etiqueta que el motor activo leería en voz alta.
4. **Pronunciación `[[respelling]]`** inline más un diccionario por idioma y por voz (JSON), con prioridad inline > voz > idioma > global.
5. **Límites de referencia**: rechazar clips con transcripción de más de 20 s y avisar fuera de 3–15 s. Si no hay transcripción, elegir automáticamente la ventana con más habla.
6. **Semilla fija por chunk** (no `seed + i`) para que la voz no derive en textos largos (#3730).
7. **Bloqueo de identidad**: guardar el take ganador como nueva referencia junto con su semilla (`--bloquear <take>`).
8. **Check audio** con ffmpeg/numpy: silencios largos, clipping y saltos de volumen con su marca de tiempo. Ya encaja con la regla 4 de AGENTS.md.
9. **Mapa de nombres "humanos"** para los parámetros avanzados (`guidance` → "influencia del prompt") en la ayuda del CLI.
10. **Ojo con las licencias**: OmniVoice tiene pesos CC-BY-NC, así que no sirve para uso comercial. El proyecto ya usa Qwen3-TTS (Apache 2.0) y Chatterbox (MIT).

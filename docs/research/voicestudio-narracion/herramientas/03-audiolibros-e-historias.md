# Audiolibros e Historias

> Investigación del 2026-11-15. Cubre **Audiobook** y **Stories**, los dos frentes del renderizador longform: gramática completa del guion, casting multivoz, emoción por línea, uniones (gaps y trim), recuperación, caché, exportación y el formato portable de personas `.ovsvoice`. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

- **Audiobook**: manuscrito con marcas → el backend lo parsea (`POST /audiobook`) y renderiza por capítulos a M4B (con capítulos embebidos) o MP3. **(leída)** `backend/api/routers/audiobook.py:1599`, `docs/electron-longform.md`.
- **Stories**: editor por líneas, con personajes, voz por línea, velocidad por línea, Auto-cast y stems por personaje. Compila un plan de capítulos y spans y lo envía a `POST /longform/render`. **(leída)** `audiobook.py:1652`.
- Un único parser canónico (`backend/services/longform_parser.py`) con su gemelo JS (`electron/src/shared/utils/longformParser.js`) y un corpus de pruebas compartido `tests/fixtures/longform_parser_cases.json`. **(leída)**

---

## 2. Cómo Se Usa

### 2.1 UI

1. Elegir una voz por defecto guardada, el idioma y el formato de salida en la tarjeta fija de setup. **(leída)** `docs/electron-longform.md`.
2. Escribir o importar el texto. Audiobook importa TXT, Markdown, EPUB y PDF; Stories además SRT y WebVTT. **Paste & Split** tiene tres presets: Sentences (40–2000 caracteres), Paragraphs (por defecto) y Chapters. **(leída)** ídem.
3. **Cast**: cada `[voice:NOMBRE]` del guion aparece en la sección Cast para asignarle un perfil. Solo se envían los nombres presentes como `voice_map`. Un personaje sin asignar lee con la voz principal. **(leída)** ídem.
4. **Stories Auto-cast**: acepta diálogo etiquetado, guion tipo screenplay y prosa atribuida. Es local, sin LLM ni red. **(leída)** ídem.
5. **Preview plan** / audición por capítulo: misma voz, cast, idioma y pronunciación que el render completo, y calienta la caché. **(leída)** ídem.
6. **Production overrides**: pasos, guidance, temperaturas, postprocesado, semilla, **Vary repeated lines**, emoción (si el motor la soporta), **Gap between lines**, **Gap between paragraphs** y **Trim engine silence**. **(leída)** ídem.
7. **Generate**: el progreso se actualiza por chunk, con porcentaje, tiempo restante y factor de tiempo real (RTF). Avisa de un posible atasco tras 6 chunks típicos sin avance (mínimo 2 min). **Stop** corta el stream. **(leída)** ídem.
8. Exportar M4B o MP3 y, opcionalmente, una **cue sheet** `.txt` (`HH:MM:SS<TAB>Título` por capítulo). **(leída)** ídem.

### 2.2 API

Audiobook (JSON, respuesta en streaming SSE). Modelo `AudiobookRequest` + `ExpressiveMixin`, `audiobook.py:99-262`: **(leída)**

```json
{
  "text": "# Capítulo 1\n[voice:Narrador] Era una noche tranquila.\n[voice:Mara] [emotion:asustada] ¿Escuchaste eso?",
  "default_voice": "<profile_id>",
  "language": "Spanish",
  "format": "mp3",
  "bitrate": "128k",
  "loudness": "podcast",
  "voice_map": {"Narrador": "<id1>", "Mara": "<id2>"},
  "lexicon": {"CapCut": "cap cut"},
  "line_gap_ms": 250,
  "paragraph_gap_ms": 350,
  "trim_edges": true,
  "num_step": 32,
  "seed": 1234,
  "vary_repeats": false
}
```

Stories (`POST /longform/render`): `chapters: [{title, spans: [{voice_id, text, pause_ms_after, speed, join, emotion}]}]` más los mismos campos. **(leída)** `audiobook.py:1622-1650`.

Otras rutas: `POST /audiobook/plan` (solo parsea), `/audiobook/preview` (`chapter_index`), `/audiobook/import`, `/audiobook/cover`, `GET /audiobook/jobs`, `POST /audiobook/resume/{job_id}`, `DELETE /longform/jobs/{id}`. **(leída)**

CLI: **(leída)** `cli/voicestudio_cli/__main__.py`

```bash
voicestudio audiobook plan --file libro.json
voicestudio audiobook render --file libro.json
voicestudio stories render --file plan.json
voicestudio audiobook jobs
voicestudio audiobook resume <job_id>
```

---

## 3. Opciones y Parámetros

### 3.1 Gramática del guion (precedencia de fuera hacia dentro)

`# capítulo → [voice:] → [emotion:] → [pause] → SSML-lite → [spell]` **(leída)** `longform_parser.py` (docstring)

| Marca | Efecto | Detalle del código |
| :--- | :--- | :--- |
| `# Título` | Abre un capítulo | Solo H1 con título no vacío; `##` sigue siendo texto. Sin título → `Chapter N` **(leída)** |
| `[voice:NOMBRE]` | Cambia de narrador hasta la siguiente marca | `[voice:]` vacío vuelve a la voz por defecto; cada capítulo reinicia la voz **(leída)** |
| `[emotion:TEXTO]` | Dirección de entrega libre | Máximo 200 caracteres, sin corchetes, sin distinguir mayúsculas. `[emotion:]` reinicia. Cada `[voice:]` y cada capítulo empiezan neutros **(leída)** |
| `[pause]`, `[pause 500ms]`, `[pause 0.5s]` | Silencio real | 350 ms por defecto, máximo 10 s, las adyacentes se suman (`omnivoice/utils/text.py`) **(leída)** |
| `[slow]…[/slow]` | `speed` 0,85 | `backend/services/ssml_lite.py` **(leída)** |
| `[fast]…[/fast]` | `speed` 1,15 | ídem **(leída)** |
| `[emphasis]…[/emphasis]` | `speed` 0,92 + marca de énfasis | ídem **(leída)** |
| `[spell]…[/spell]` | Deletrea por grafemas | ídem **(leída)** |

Reglas SSML-lite: las etiquetas se anidan y gana la más interna; una etiqueta sin cerrar dura hasta el fin de la línea; un cierre suelto se ignora. **(leída)** `ssml_lite.py`.

**Conflicto** (Android): la app móvil usa otra sintaxis, `[pause:0.5]` y `[speed:1.25]` al inicio de línea (i18n `mobile.books.controls_hint`, pausas hasta 30 s). No coincide con la del escritorio (`[pause 0.5s]`, máximo 10 s). **(leída)**

### 3.2 Uniones entre líneas

| Campo | Rango | Defecto | Nota |
| :--- | :--- | :--- | :--- |
| `line_gap_ms` | 0–5000 | 0 | Silencio exacto entre líneas **(leída)** |
| `paragraph_gap_ms` | 0–5000 | 0 | Entre párrafos (línea en blanco) **(leída)** |
| `trim_edges` | bool | false | Recorta lo que esté por debajo de -40 dBFS en ambos extremos y deja 40 ms **(leída)** `docs/expressive-speech.md` |

- Recomendación de la doc: ~250 ms entre líneas y ~350 ms entre párrafos. Ojo: el valor por defecto es 0, así que hay que enviarlos explícitamente. **(leída)**
- Un `[pause]` explícito **reemplaza** el gap de línea, no se suma. Un `[voice:]` cuenta como frontera de línea. `[slow]` y similares no crean gap interno. **(leída)**
- La unión de un capítulo añade como máximo 15 minutos de silencio; si se supera, la petición falla antes de sintetizar. **(leída)**

### 3.3 Producción y salida

| Campo | Valores | Fuente |
| :--- | :--- | :--- |
| `format` | `m4b` (por defecto) o `mp3` | `audiobook.py:249` **(leída)** |
| `loudness` | `off`, `acx` (-19 LUFS, -3 dBTP, LRA 11), `podcast` (-16 LUFS, -1,5 dBTP, LRA 11) | `backend/services/longform_render.py:629-630` **(leída)** |
| `metadata` | title, author, narrator, year, genre, description | `audiobook.py` **(leída)** |
| `num_step` | 1–512; sin enviar = 32 (preset longform) | `ExpressiveMixin` **(leída)** |
| `seed` | 0–2³²-1; prioridad: libro > semilla fijada del perfil > aleatoria | ídem **(leída)** |
| `emo_text`, `emo_alpha`, `emo_vector` | Solo IndexTTS2 | ídem **(leída)** |
| `vary_repeats` | Un take distinto para cada línea repetida | ídem **(leída)** |

### 3.4 Emoción por línea según el motor

| Motor | Aplicación |
| :--- | :--- |
| IndexTTS2 | Como `emo_text` (intensidad del libro o 0,6). Lo reduce a 8 emociones: `terrified, whispering` suena "afraid" a volumen normal **(leída)** |
| CosyVoice 3 | Modo instrucción. Ignora la entrega de la referencia y puede alejarse de la voz clonada **(leída)** |
| VoxCPM2 | Se suma a la dirección escrita de la voz **(leída)** |
| Otros (incl. OmniVoice) | Se ignora y el chequeo del guion lo avisa. Nunca se lee en voz alta **(leída)** |

---

## 4. Ejemplos

**Storytelling corto para reel, multivoz:**

```text
# La casa del final de la calle
[voice:Narrador] Nadie entraba a esa casa desde hacía veinte años. [pause 0.6s]
Hasta esa noche.

[voice:Lucía] [emotion:nerviosa] ¿Estás seguro de que está vacía?
[voice:Tomás] [emotion:confiado] Completamente. [pause 0.3s] [slow]Confía en mí.[/slow]
[voice:Narrador] La puerta se abrió sola. [pause 1s]
```

**Tutorial con siglas y énfasis:**

```text
# Paso 1
Exporta en [spell]MP4[/spell] con códec [spell]H264[/spell].
[emphasis]Nunca[/emphasis] subas el archivo sin revisar el audio. [pause 0.4s]
[fast]Rápido: Control más E, elige el preset, y listo.[/fast]
```

**Publicidad (cambio de emoción al inicio de cada frase, nunca a mitad):**

```text
[voice:Locutora] [emotion:entusiasta] ¡Llegó la nueva versión!
[emotion:calmada] Más rápida, más simple, y gratis para siempre.
```

Cambiar la emoción a mitad de frase la parte en renders separados y pierde la entonación natural. **(leída)** `docs/expressive-speech.md`.

---

## 5. Tips y Trucos

- Activar los gaps y el trim explícitamente. Sin ellos, las pausas entre líneas son las colas aleatorias de cada motor. **(leída)**
- **Fill pauses with room tone** (Settings → Pronunciation dictionary → Pauses, o `OMNIVOICE_PAUSE_FILL=room_tone`) evita el efecto "gate" de los ceros digitales ([#3611](https://github.com/debpalash/VoiceStudio/issues/3611) midió el piso de ruido en -53 dBFS). **(leída)**
- La caché por capítulo se indexa por guion, voz y ajustes: editar una línea re-renderiza solo lo que cambió. Re-bloquear una voz cambia el nombre del archivo y la invalida. **(leída)** `docs/expressive-speech.md`, `profiles.py` lock.
- **Vary repeated lines** está apagado por defecto para que el libro sea reproducible byte a byte. **(leída)**
- La recuperación (**Resume**) reutiliza los capítulos ya hechos y conserva el checkpoint original hasta terminar. **Open chapter cache** abre la carpeta. **(leída)** `docs/electron-longform.md`.
- **Stems** en Stories genera un WAV por personaje, útil para mezclar en el editor de video. **(leída)**
- El diccionario por voz **no** aplica a los capítulos de Audiobook: estos usan solo el `lexicon` del proyecto. **(leída)** `docs/expressive-speech.md`.
- Para un susurro asustado: diseñar la voz con `whisper`, bloquearla y renderizar con IndexTTS2 más `[emotion:terrified]`. **(leída)**

### Personas `.ovsvoice`

ZIP con `manifest.json`, `metadata.json`, `preview.wav` (con marca de agua AudioSeal si está instalado), `consent.json` opcional y `ref_audio.*` y `locked_audio.*` (se omiten si se desmarca "Include voice clip"). La licencia SPDX es solo metadato. Exportar e importar es 100 % local. **(leída)** `docs/persona-format.md`.

---

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#3417](https://github.com/debpalash/VoiceStudio/issues/3417) | Cerrado | Libro de 34k palabras (~3 h 41 min) seguía corriendo tras más de 8 h en un M5 Pro. Motivó el ETA y la detección de atascos **(leída)** |
| [#4090](https://github.com/debpalash/VoiceStudio/issues/4090) | Abierto | En Mac, Stories con un párrafo de 3–4 frases tarda ~3 min y vuelve al Home **(leída)** |
| [#4071](https://github.com/debpalash/VoiceStudio/issues/4071) | Cerrado | La salida MP3 de audiobook daba 404 (una ruta tapaba los estáticos); M4B sí funcionaba **(leída)** |
| [#2535](https://github.com/debpalash/VoiceStudio/issues/2535) | Cerrado | Re-bloquear una voz reproducía capítulos cacheados del take anterior **(leída)** |
| [#2536](https://github.com/debpalash/VoiceStudio/issues/2536) | Cerrado | Un audiobook cancelado quedaba marcado como "running" **(snippet)** |
| [#2508](https://github.com/debpalash/VoiceStudio/issues/2508) | Cerrado | Manuscritos con CR perdían los capítulos **(snippet)** |
| [#4201](https://github.com/debpalash/VoiceStudio/issues/4201) | Abierto | En Android, importar un EPUB/TXT grande rompe el editor **(snippet)** |

---

## 7. Qué Dice la Comunidad

- **A**: [#3422](https://github.com/debpalash/VoiceStudio/issues/3422) recoge pedidos de Discord ("the audiobook lacks emotion", respiraciones a demanda). [#3417](https://github.com/debpalash/VoiceStudio/issues/3417): un libro infantil tardó 19–22 min. **(leída)**
- **B**: [andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) cita a un comentarista: ~15 s de audio en 25–30 s en una RX 590, "fine for audiobooks and dubbing, not … live". **(leída)**
- **C**: listados (besthub.dev, everydev.ai) mencionan EPUB → audiolibro por capítulos sin pruebas. No encontré ninguna reseña práctica independiente de audiolibros. **(snippet)**

---

## 8. Qué Sirve para social-videos

1. **Adoptar la gramática** en el guion de `narration/tts.py`, compatible con la de VoiceStudio para poder intercambiar guiones: `# sección`, `[voice:NOMBRE]`, `[emotion:...]`, `[pause Xs]`, `[slow]`, `[fast]`, `[emphasis]`, `[spell]`. Precedencia y reglas de reinicio como en §3.1. Implementarla desde cero; el parser es corto.
2. **`[emotion:]` → instrucción del motor**: en Qwen3-TTS (que acepta `instruct`) se mapea directo; en Chatterbox se puede traducir a `exaggeration`/`cfg`. Reiniciar en cada `[voice:]`.
3. **Gaps explícitos + trim a -40 dBFS** con colchón de 40 ms: valores por defecto de 250/350 ms para narración de video y `[pause]` que reemplaza el gap.
4. **Caché por línea** con clave = hash(texto, voz, ruta de referencia, semilla, parámetros), para re-renderizar solo las líneas editadas en las iteraciones de evaluación.
5. **Presets de loudness** (`podcast` -16 LUFS / -1,5 dBTP; para redes, -14 LUFS es lo habitual) con `ffmpeg loudnorm` al final.
6. **Cue sheet** (`HH:MM:SS<TAB>Título`) por sección: sirve para marcadores de edición o capítulos de YouTube.
7. **Stems por personaje** para la mezcla en el editor.
8. **Validar el cast antes de renderizar** (personaje sin voz → error claro) y una vista previa por sección.

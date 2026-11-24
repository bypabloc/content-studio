# Diseño de Voz

> Investigación del 2026-11-15. Cubre **Voice Design**: taxonomía exacta de atributos de OmniVoice, motores de texto libre, mapeo de descripciones, semilla y paso de diseño a voz guardada (y de ahí a clon bloqueado). Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

- Se crea una voz **sin audio de referencia**, describiendo al hablante. En OmniVoice se hace con el parámetro `instruct`: atributos separados por comas, uno por categoría. **(leída)** `docs/voice-design.md`.
- Hay dos maneras de leer la descripción, según el motor (`instruct_vocabulary` en `GET /engines/tts`):
  - `"tags"` (familia OmniVoice): lista cerrada de atributos.
  - `"freeform"` (Qwen3-TTS VoiceDesign vía MLX-Audio, VoxCPM2, audio.cpp): el texto llega tal cual.
  **(leída)** `docs/voice-design.md` §"Other engines".
- No diseñan (`supports_voice_design=false`, y `/generate` responde 422): IndexTTS2, MOSS-TTS v1.5, MOSS-TTS-Nano, dots.tts, Confucius4, GPT-SoVITS, Supertonic-3, OmniVoice GGUF, PocketTTS, KittenTTS y Sherpa-ONNX. **(leída)** ídem. El issue [#4080](https://github.com/debpalash/VoiceStudio/issues/4080) (cerrado) pidió diseño para omnivoice-gguf; **conflicto** posible con la doc, **no verificado**.

---

## 2. Cómo Se Usa

### 2.1 En la UI

1. Abrir **Design** desde la barra lateral de clonación o la búsqueda de comandos. **(leída)** `docs/electron-voice-design.md`.
2. Escribir una descripción ("Describe the voice, or pick a starting point") o elegir un **Starting point** (personalidad o demo). Cualquiera de los dos rellena los detalles. **(leída)** i18n `clone.describe_hint`, `clone.starting_points`.
3. Ajustar los rasgos a mano. Un rasgo elegido a mano se mantiene hasta que la descripción diga otra cosa sobre ese mismo rasgo. **Reset to description** descarta todos los ajustes manuales. **(leída)** `docs/voice-design.md`.
4. Escribir el guion y sintetizar. La semilla se mantiene fija mientras se ajustan rasgos; **New seed** crea otra identidad. **(leída)** `docs/electron-voice-design.md`, i18n `clone.seed_reroll`.
5. **Save as voice profile**: guarda la semilla y el estado validado de los atributos. Si el motor está cargado, renderiza en ese momento la muestra de identidad; si no, la guarda pendiente hasta la primera previsualización. **(leída)** `docs/voice-design.md`.
6. Al elegir luego esa voz guardada, se re-renderiza **desde su muestra guardada**, así que suena igual siempre. Cambiar un detalle, la descripción o la semilla la convierte en un borrador sin guardar. **(leída)** ídem.
7. Gallery: **Use voice** materializa un arquetipo (catálogo de 1.126 entradas durante el desarrollo) como perfil de diseño y abre Design. **Open in Design** pasa los atributos de un preset de Community. **(leída)** `docs/electron-gallery.md`.

### 2.2 API

Mapear una descripción sin guardar nada (`backend/api/routers/describe_voice.py`). El mapeador es determinista por palabras clave, sin modelo ni red:

```bash
curl -X POST http://127.0.0.1:3900/design/describe -H 'Content-Type: application/json' \
  -d '{"description":"female, young adult, low pitch, warm and slightly raspy"}'
# → {"attrs":{...},"instruct":"female, young adult, low pitch","matched":[...],"unmatched":["warm","slightly raspy"]}
```

Crear el perfil de diseño (`POST /profiles` con `kind=design` y `vd_states` JSON obligatorio, `profiles.py:126`):

```bash
curl -X POST http://127.0.0.1:3900/profiles -F name="Locutora joven" -F kind=design \
  -F vd_states='{"Gender":"female","Age":"young adult","Pitch":"low pitch","Style":"Auto","EnglishAccent":"Auto","ChineseDialect":"Auto"}' \
  -F instruct="female, young adult, low pitch" -F seed=76785 -F language=Spanish
```

Las claves exactas de `vd_states` salen de `CATEGORY_ORDER` (#983); las del ejemplo están **no verificadas**. Sin `seed` el servidor usa 42. **(leída)** docstring de `create_profile`.

Generar diseñando al vuelo: `POST /generate` con `instruct=` y sin `ref_audio`. Si `instruct` o `seed` difieren del perfil de diseño, la app diseña desde la petición y el take no se archiva bajo ese perfil. **(leída)** `docs/voice-design.md`.

### 2.3 CLI y MCP

```bash
voicestudio voices describe "male, middle-aged, low pitch, american accent"
voicestudio voices design --name "Narrador grave" --description "male, middle-aged, low pitch"
```

`voices design` llama a `/design/describe` y falla si no hay coincidencias. Después crea el perfil con `vd_states` e `instruct`. **(leída)** `cli/voicestudio_cli/__main__.py:721-735`.

MCP: `describe_voice` (no guarda nada) y `design_voice` (crea el perfil; rechaza descripciones sin ningún atributo reconocido). **(leída)** `docs/mcp.md`.

---

## 3. Opciones y Parámetros

### 3.1 Taxonomía exacta OmniVoice (un valor por categoría)

| Categoría | Valores (inglés) | Nota |
| :--- | :--- | :--- |
| Gender | `male`, `female` | **(leída)** |
| Age | `child`, `teenager`, `young adult`, `middle-aged`, `elderly` | **(leída)** |
| Pitch | `very low pitch`, `low pitch`, `moderate pitch`, `high pitch`, `very high pitch` | **(leída)** |
| Style | `whisper` | El único estilo; no hay `[happy]` ni `[sad]` **(leída)** |
| English Accent | `american`, `british`, `australian`, `canadian`, `indian`, `chinese`, `korean`, `japanese`, `portuguese`, `russian` + ` accent` | Solo actúa con texto en inglés **(leída)** |
| Chinese Dialect | 河南话, 陕西话, 四川话, 贵州话, 云南话, 桂林话, 济南话, 石家庄话, 甘肃话, 宁夏话, 青岛话, 东北话 | Solo con texto en chino **(leída)** |

Fuente: `docs/voice-design.md`. No hay acento español ni latinoamericano en la taxonomía. Para español, el acento lo da el idioma del texto. **(leída)**

### 3.2 Reglas del `instruct`

| Regla | Detalle |
| :--- | :--- |
| Separador | `,` en inglés, `，` en chino; la mezcla se corrige sola |
| Mayúsculas | Indiferente; se normaliza a minúsculas |
| Omitir categorías | Válido; el modelo completa (`"female"` solo funciona) |
| Idioma del instruct | Inglés, chino o mezcla |

### 3.3 Semilla

| Aspecto | Comportamiento | Fuente |
| :--- | :--- | :--- |
| Semilla = identidad | Fija mientras se ajustan rasgos; New seed = otra voz | `docs/electron-voice-design.md` **(leída)** |
| Motores con RNG propio | VoxCPM2, CosyVoice, audio.cpp, MLX-Audio y el sidecar de OmniVoice reciben la semilla en cada petición | `docs/voice-design.md` **(leída)** |
| Bloqueo de un perfil de diseño | Conserva la semilla del diseño, no la del take (#3254) | `profiles.py` lock **(leída)** |

---

## 4. Ejemplos

Prompts `tags` para OmniVoice (el guion va en español; el acento sale del texto):

| Uso | `instruct` |
| :--- | :--- |
| Tutorial técnico, voz neutra | `male, young adult, moderate pitch` |
| Storytelling nocturno | `female, middle-aged, low pitch` |
| ASMR o intro misteriosa | `female, young adult, low pitch, whisper` |
| Publicidad juvenil | `female, teenager, high pitch` |
| Abuelo narrador | `male, elderly, very low pitch` |
| Reel en inglés | `male, young adult, moderate pitch, american accent` |

Prompts `freeform` (VoxCPM2, Qwen3-TTS VoiceDesign):

```text
Voz masculina de unos 35 años, cálida y cercana, ritmo pausado, como un presentador de podcast de tecnología.
Locutora enérgica de comercial de radio, sonrisa audible, frases cortas y contundentes.
```

Con un motor `freeform`, los rasgos elegidos a mano se añaden después de la descripción como pistas extra. Los que la app solo dedujo del texto no se repiten. **(leída)** `docs/voice-design.md`.

**De diseño a clon reutilizable** (receta de `docs/expressive-speech.md` §"Per-line emotion"): **(leída)**

1. Diseñar en OmniVoice con Style `whisper`.
2. Guardar y pulsar **Lock voice identity**.
3. Asignarla en **Cast**.
4. Renderizar con IndexTTS2, que clona el audio del take bloqueado y le suma emoción: `[voice:Susurro] [emotion:terrified] ¿Escuchaste eso?`

---

## 5. Tips y Trucos

- Omitir atributos amplía la variedad. Para una identidad estable, fijar la semilla y guardar. **(leída)**
- Probar varias semillas con el mismo `instruct`: cada semilla es "otra persona" con los mismos rasgos. **(leída)**
- `voices describe` muestra en `unmatched` las palabras ignoradas por el motor `tags`. Sirve para no fiarse de adjetivos que no llegan al modelo. **(leída)** `describe_voice.py`.
- Una voz de diseño guardada funciona en motores de clonación a través de su muestra. KittenTTS y Sherpa-ONNX no, porque solo usan presets. **(leída)** `docs/voice-design.md`.
- Gallery rechaza las previsualizaciones silenciosas o con zumbido tonal. **(leída)**

---

## 6. Problemas Conocidos

| Issue | Estado | Resumen |
| :--- | :--- | :--- |
| [#3254](https://github.com/debpalash/VoiceStudio/issues/3254) | Cerrado | Guardar un diseño descartaba la semilla del usuario (renderizaba con 42) y la voz guardada sonaba distinta **(leída)** |
| [#2389](https://github.com/debpalash/VoiceStudio/issues/2389) | Cerrado | Las descripciones libres para Qwen3-TTS y VoxCPM2 se recortaban a la taxonomía de OmniVoice **(leída)** |
| [#3730](https://github.com/debpalash/VoiceStudio/issues/3730) | Cerrado | En guiones largos la voz diseñada cambiaba entre trozos (semilla + i) **(leída)** |
| [#1739](https://github.com/debpalash/VoiceStudio/issues/1739) | Cerrado | Fonemas finales fragmentados en voces diseñadas **(leída)** |
| [#983](https://github.com/debpalash/VoiceStudio/issues/983) | — | `vd_states` parcial rompía el panel; ahora el servidor exige todas las categorías (comentario en `profiles.py`) **(snippet)** |

---

## 7. Qué Dice la Comunidad

- **B**: la reseña de [andrew.ooo](https://andrew.ooo/posts/voicestudio-review-local-elevenlabs-alternative/) solo enumera el diseño como capacidad, sin prueba propia. **(leída)**
- **C**: [techsy.io](https://techsy.io/en/blog/omnivoice-review) prueba el modelo k2-fsa OmniVoice v0.1.5, no la app. **(snippet)**
- No encontré tutoriales en video ni foros con resultados de diseño en español. **No verificado** que la taxonomía funcione bien con texto en español.

---

## 8. Qué Sirve para social-videos

1. **Perfil = descripción + semilla + muestra renderizada**. Al guardar un diseño, renderizar una muestra fija y usarla después como referencia de clonación. Así la voz no depende de la semilla en cada corrida. Aplica a Qwen3-TTS VoiceDesign si se añade al CLI.
2. **Mapeador determinista descripción → atributos** con salida `matched`/`unmatched`, para avisar qué palabras no llegan al modelo (útil en `--estilo`).
3. **Distinguir motores `tags` y `freeform`** en la tabla de modelos de `tts.py` y validar antes de gastar GPU (422 temprano).
4. **Reutilizar el patrón "diseñar → bloquear → clonar con otro motor"**: generar con un motor que diseña y clonar ese WAV con Chatterbox para tener más control expresivo.
5. **Semilla fija por voz** guardada en los metadatos de la voz, al lado del `.wav` en `narration/voz/`.

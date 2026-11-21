# server/data/narration/ — Narración TTS local con clonación de voz

Genera narración en **español neutro latinoamericano** (o en inglés con `--language en`) clonando una voz de referencia, 100 % local en una **RTX 4060 Laptop (8 GB VRAM)**. Sin APIs ni costo por uso. Siete motores, en orden de preferencia: **VoxCPM2** (recomendado), **CosyVoice 3** (segunda opción), Qwen3-TTS (1.7B y 0.6B), Chatterbox V3, OmniVoice e IndexTTS 2.5.

```
server/data/narration/
├── README.md            este documento
├── voices/               catalog.json (versionado) + <voz>/<estilo>.wav construidos (gitignoreado)
├── docs/
│   ├── formato-guion.md cómo escribir el texto: pausas, estilo, emoción, gestos, pronunciación
│   └── scripts/         cómo grabar las referencias de voz: un guion por estilo
└── reference/           referencias de voz y perfiles locales (gitignoreado)
│   ├── emotions/        (opcional) clips de emoción para IndexTTS
│   └── prueba/          referencia de prueba (expert.wav + .txt) mientras no grabes las tuyas
```

Los entornos virtuales y los pesos de los motores se guardan en la carpeta de motores elegida en Ajustes > Almacenamiento. Por defecto es `%LOCALAPPDATA%\Content Studio\engines`; ya no viven dentro de `server/data/narration/`.

El código está en `server/src/content_studio/narration/` (ver la arquitectura en [AGENTS.md](../../../AGENTS.md#arquitectura)) y se lanza con `uv run studio narration tts` y `uv run studio narration voices`; `grabar` tiene su propio comando ([§5](#5-grabar-las-referencias)). Cada trabajo sale en `out/narration/<AAAA-MM-DD>-<id>-<slug>/` (gitignoreado) con su `params.json`, y su log va a `logs/jobs/<id>.log`: `studio` no acepta `--output`. Dentro de esa carpeta, cada toma deja un `.wav` y un `.json` con sus metadatos.

**Todavía no hay referencias grabadas** en `reference/<estilo>.wav`: hasta que las grabes (ver [docs/scripts/](docs/scripts/README.md)), usa una **voz libre del catálogo** con `--voice` ([§5.1](#51-voces-libres-del-catálogo---voice)) por ejemplo `--voice yesid`, que tiene el consentimiento de su dueño.

---

## 1. Modelos elegidos

Filtro aplicado: modelos abiertos que **soportan español** (o inglés), que **clonan voz** y que **caben en los 8 GB de la GPU**. El español neutro se consigue con una referencia neutra: ningún modelo trae un "neutro" de fábrica.

### 1.1 Qwen3-TTS y Chatterbox (investigación de octubre de 2026)

| | **Qwen3-TTS Base** (Alibaba, ene-2026) | **Chatterbox Multilingual V3** (Resemble AI) |
|---|---|---|
| Tamaños | 0.6B y 1.7B | 0.5B |
| Licencia | **Apache 2.0** (uso comercial OK) | **MIT** (uso comercial OK) |
| Idiomas | 10, incluye español (`Spanish`) | 23, incluye español (`es`) |
| Clonación | 3 s+ de audio, mejor con transcripción (modo ICL) | ~10 s de audio, sin transcripción |
| Español por defecto | Latinoamericano, no castellano | Depende de la referencia |
| Control de estilo | **No** en Base (`instruct` solo existe en CustomVoice/VoiceDesign, que no clonan) | `exaggeration`, `cfg_weight`, `temperature` |
| Audio | 24 kHz | 24 kHz |

**Lo que dice la comunidad**

- **Qwen3-TTS**: WER multilingüe de ~1.8 % y similitud de hablante de 0.79, por delante de ElevenLabs Multilingual v2 y MiniMax. Problema conocido: **acento inglés que se cuela** en español, sobre todo con Voice Design ([discusión #230](https://github.com/QwenLM/Qwen3-TTS/discussions/230)). Solución: clonar una referencia nativa, como hace este script. Ya existe un [pack de 14 voces en español](https://github.com/QwenLM/Qwen3-TTS/discussions/300).
- **Chatterbox V3**: mejor similitud de hablante y menos alucinaciones que la versión multilingüe anterior. Problema conocido: **arrastra el acento** del idioma de la referencia. Resemble recomienda `cfg_weight=0` si la referencia está en otro idioma. Con una referencia en español neutro no aplica.

### 1.2 Motores añadidos (investigación de noviembre de 2026)

| | **OmniVoice** (k2-fsa) | **VoxCPM2** (OpenBMB) | **IndexTTS 2.5** (IndexTeam) | **CosyVoice 3** (FunAudioLLM) |
|---|---|---|---|---|
| Licencia | CC-BY-NC + Higgs Audio 2 | Apache 2.0 | bilibili Model Use License | Apache 2.0 (la tarjeta del modelo dice "academic purposes") |
| Uso comercial | **No** (solo personal) | Sí | **No** (solo personal) | Sí, según la licencia del código; revisa la tarjeta del modelo |
| Clonación | Con transcripción (obligatoria) | Hi-Fi con transcripción, o controlable sin ella | Sin transcripción | Con transcripción (obligatoria) |
| Emoción | Por referencia (`energetic`, `dramatic`…) | Instrucción en inglés (controlable) | Vector de 8 emociones o clip | Instrucción (`instruct2`) |
| Gestos | `[risa]`, `[suspiro]` | No | No | `[risa]`, `[suspiro]`, `[respiro]`, énfasis |
| Audio | 24 kHz | 48 kHz | 22.05 kHz | 24 kHz |

Los gestos y las emociones de cada motor se traducen por motor (`texto/traducir.py`); la tabla completa está en [docs/formato-guion.md](docs/formato-guion.md#traducción-por-motor).

**Descartados** (ver la investigación completa en [docs/research/voicestudio-narracion/](../../../docs/research/voicestudio-narracion/README.md)): Voxtral TTS (≥10 GB), Higgs Audio v3 (no comercial y lento en 8 GB), F5-TTS, XTTS v2 y Fish S1-mini (licencias no comerciales), Kokoro (acento inglés, no clona), Dia, Orpheus y Breeze TTS 2 (sin español).

**Orden de preferencia en este proyecto**: 1) `voxcpm2` (motor estrella), 2) `cosyvoice3`, 3) `qwen-1.7b`, 4) `qwen-0.6b`, 5) `chatterbox`, y al final los no comerciales `omnivoice` e `indextts`. Es el orden del registro de motores (`engines/registry.py`). Ver [§7](#7-problemas-conocidos).

---

## 2. Instalación

Instala los motores desde **Motores** en la app o con el CLI. Cada receta crea un entorno aislado y fija sus paquetes, versiones y revisiones del modelo. La aplicación guarda los venvs y los pesos en la carpeta configurada para motores; puedes cambiarla en Ajustes > Almacenamiento.

```powershell
uv run studio engines list
uv run studio engines install qwen-0.6b
uv run studio engines verify qwen-0.6b
uv run studio engines repair qwen-0.6b
uv run studio engines uninstall qwen-0.6b
```

Las recetas versionadas están en `server/src/content_studio/engines/recipes/`. El instalador descarga los pesos bajo demanda y reanuda los pasos incompletos. En Windows, si falta Git o FFmpeg, la app puede ofrecer instalarlos con winget. Para consultar los identificadores admitidos, ejecuta `uv run studio engines list`.

---

## 3. Uso

El script se re-ejecuta solo con el venv que corresponde, así que basta con `uv run studio` desde la raíz del repo:

```bash
# Texto directo, referencia por defecto (server/data/narration/reference/<estilo>.wav)
uv run studio narration tts --model qwen-0.6b --style friendly \
  --text "Hola, bienvenidos al canal. Hoy te muestro cómo editar un video en un minuto."

# Guion desde archivo, modelo grande
uv run studio narration tts --model qwen-1.7b --style expert \
  --file guion.txt

# Con una voz libre del catálogo, aprobada en los 12 estilos (§5.1)
uv run studio narration tts --model cosyvoice3 --voice yesid --style dramatic \
  --text "Nadie sabía lo que había pasado esa noche."

# Mientras no haya grabaciones propias: una voz libre con consentimiento
uv run studio narration tts --model qwen-0.6b --voice yesid \
  --text "Hola, esto es una prueba."

# Estilo y emoción por párrafo, semilla fija y evaluación (ver formato-guion.md)
uv run studio narration tts --model omnivoice --ref server/data/narration/voz --file guion.txt --seed 7 --evaluate

# En inglés: el estilo por defecto es neutral-en (reference/neutral-en.wav)
uv run studio narration tts --model chatterbox --language en --file guion-en.txt

# Varios guiones JSON en una corrida (estilo e id salen de cada JSON)
uv run studio narration tts --model qwen-0.6b --file guiones/*.json
```

Por cada guion imprime la semilla, la duración, el lote usado, la velocidad y el pico de VRAM. El tiempo del primer guion incluye la carga del modelo:

```
Semilla: 7
out/narration/<AAAA-MM-DD>-<id>-<slug>/qwen-0.6b-expert.wav (47.7 s, qwen-0.6b, experta, lote 3) | generación 44.6 s, 1.07x tiempo real | pico VRAM 5.70 GiB
```

### Desde la app (sección Narración)

La app (`bun run --cwd client tauri dev`) tiene la misma narración con interfaz:

- **Guion**: el editor avisa en vivo de lo que no cumple la regla de [formato-guion.md](docs/formato-guion.md#reglas-obligatorias). Los avisos no bloquean: «Generar» encola igual. Se importan `.txt` y `.json` con «Importar» o soltándolos sobre la ventana; cada archivo es un trabajo.
- **Opciones**: motor, voz, estilo e idioma, cada uno con ★ en lo recomendado y recordado. Un motor no comercial pide aceptar su licencia la primera vez (queda guardada por motor). «Avanzado» tiene la masterización, los LUFS, la semilla, el lote (solo los motores que lo admiten), la evaluación con whisper y los reintentos.
- **Generar**: el botón o Ctrl+Enter encola el trabajo.
- **Resultado**: la última toma, con su reproductor (onda), su LUFS y su pico. Con evaluación, cada párrafo muestra lo que whisper oyó distinto (cambios, faltas y sobras) y los silencios y ritmos que avisa el motor. «Regenerar» encola un bloque nuevo sobre esa toma; la toma nueva comparte el texto.
- **Comparar**: las tomas del mismo texto, en columnas. «Elegir» marca una con ★. Al reproducir una, las demás se pausan. Espacio reproduce o pausa, salvo al escribir.

### Flags

| Flag | Valores | Por defecto | Qué hace |
|---|---|---|---|
| `--model` | `voxcpm2` (recomendado), `cosyvoice3`, `qwen-1.7b`, `qwen-0.6b`, `chatterbox`, `omnivoice`, `indextts` | `voxcpm2` | Motor a usar ([§1](#1-modelos-elegidos)) |
| `--ref` | `.wav` o carpeta | `server/data/narration/voz` | Con una carpeta usa `<estilo>.wav`; la transcripción va en el `.txt` homónimo. Un `[estilo:]` sin su `.wav` detiene el script antes de generar |
| `--voice` | voces aprobadas del catálogo | — | Usa `server/data/narration/voices/<voz>/` en lugar de `--ref`. Solo acepta voces aprobadas en **todos** los estilos; el idioma de la voz tiene que coincidir con `--language` ([§5.1](#51-voces-libres-del-catálogo---voice)) |
| `--style` | `friendly`, `soft`, `expert`, `clear`, `steady`, `neutral`, `energetic`, `dramatic`, `sad`, `intimate`, `whisper`, `neutral-en` | el `estilo` del JSON, o `expert` (`neutral-en` con `--language en`) | Referencia y parámetros del estilo. Un `[estilo:]` dentro del texto lo cambia desde ese punto |
| `--text` | texto | uno de los dos | Lo que se narra |
| `--file` | uno o varios `.txt` o `.json` | uno de los dos | Guiones a narrar. Con varios, el modelo se carga una sola vez. Formato JSON en [docs/formato-guion.md](docs/formato-guion.md#guiones-en-json) |
| `--batch` | entero | automático | Frases por pasada en Qwen: más rápido, pero usa más VRAM |
| `--seed` | entero | aleatoria | Semilla base: cada bloque de una ronda usa la misma. Se imprime y queda en el `.json`. Los reintentos usan base + n |
| `--master` | `voz`, `no` | `voz` | `voz`: pasa-altos de 70 Hz y loudness de `--lufs`, con pico de −1.5 dBTP. `no`: salida del motor sin procesar |
| `--lufs` | número | -16 | Loudness objetivo de `--master voz` |
| `--language` | `es`, `en` | `es` | Idioma del motor y de whisper. Con `en`, el estilo por defecto es `neutral-en` |
| `--evaluate` | — | apagado | Al terminar, transcribe cada salida con whisper y la compara párrafo por párrafo con el texto pedido (ver abajo) |
| `--retries` | entero | 0 | Con `--evaluate`: rondas en las que se regeneran **solo** los párrafos con observaciones, y se vuelven a evaluar |

### Salidas

- Dentro de la carpeta del trabajo, el nombre por defecto es `<id>-<modelo>.wav` (guion JSON) o `<modelo>-<estilo>.wav`.
- **`.wav`**: PCM de 24 bits a la frecuencia nativa del motor. Con `--master voz`, a `--lufs` y con pico de −1.5 dBTP; con `--master no`, sin procesar.
- **`.json`** (junto al `.wav`): motor, licencia y `comercial`; `semilla` y `semillas_por_ronda`; por bloque, el texto del guion, el texto enviado al motor, el estilo, la referencia con su SHA-256, la emoción, el modo, la semilla, los avisos y los tiempos de inicio y fin; `master` (lo medido en la masterización, y el techo de pico usado en `techo_tp`); `evaluacion`, si usaste `--evaluate`; y `version_tts` (el commit del script, con `-dirty` si había cambios sin confirmar).

### Estilo y emoción por párrafo

Un guion puede cambiar de estilo y de emoción en cualquier punto, con `[estilo: dramatica]` y `[emocion: triste 0.4]`. Además, `[risa]`, `[suspiro]`, `[respiro]` y `[enfasis]palabra[/enfasis]` se traducen para cada motor. La sintaxis completa, las emociones y cómo las aplica cada motor están en **[docs/formato-guion.md](docs/formato-guion.md#estilo-y-emoción-por-párrafo)**.

### Evaluar las salidas (`--evaluate`)

```bash
uv run studio narration tts --model qwen-0.6b --file guiones/*.json --evaluate
```

Después de generar todo, libera el modelo de la VRAM y transcribe con whisper `medium` **cada párrafo por separado**, todos en una sola llamada. Con el audio completo, whisper a veces se saltaba media oración o pasaba palabras al párrafo vecino. Por cada guion imprime `OK` o `REVISAR` con lo que encontró:

```
REVISAR out/narration/<AAAA-MM-DD>-<id>-<slug>/011-nunez-sin-tilde-qwen-0.6b.wav
          párrafo 2: cambio "cuenta" -> "cuento"
          párrafo 4: silencio de 1.6 s dentro del párrafo
OK      out/narration/<AAAA-MM-DD>-<id>-<slug>/017-tu-especialidad-hace-sus-cuentas-qwen-0.6b.wav
          aviso, párrafo 5: ritmo 2.0 palabras/s (mediana 3.3)
```

| Revisa | Cómo | ¿Es error? |
|---|---|---|
| Palabras que faltan, sobran o cambian | Compara cada párrafo con lo que oyó whisper. Antes normaliza tildes, signos, números y siglas ("pe de efe" = "PDF" = "P D F"). Las marcas del guion no cuentan | Sí |
| Silencios que nadie pidió | Silencios de más de 1.3 s **dentro** de un párrafo. Las pausas entre párrafos no se revisan, porque las inserta el script | Sí |
| Ritmo | Párrafos con menos de 0.7× o más de 1.4× palabras por segundo que la mediana del guion, sin contar las pausas | No: es un **aviso**, porque una lista o una pregunta se leen distinto a propósito |

Whisper no oye entonación ni acento, y a veces se equivoca él mismo. Las palabras que se escriben distinto pero suenan igual ("guasap" y "WhatsApp", "estok" y "stock", "de pendiente" y "dependiente") y los números ("siete" y "7") no cuentan como error. Un `REVISAR` significa "escucha este párrafo", no "está mal".

Con `--language en`, whisper evalúa en inglés y **no se comparan los números ni las unidades de moneda o porcentaje**: whisper los escribe como cifras o símbolos ("seven dollars" → "$7"). Es una simplificación con límite conocido: un error de número en inglés no se detecta.

El `.json` de cada guion guarda `evaluacion`: las observaciones, las rondas usadas y si quedó sin errores. Con OmniVoice y sin `--evaluate`, `narration tts` lo sugiere, porque omite palabras con frecuencia.

**Reintentos.** El modelo muestrea al azar: la misma frase a veces sale bien y a veces no (por ejemplo, "parto" → "parte" en un 40–60 % de las generaciones). Con `--retries N`, después de evaluar se regeneran solo los párrafos con observaciones, con la semilla de la ronda (base + n), se rearma el audio (el resto no se toca) y se vuelve a evaluar, hasta N rondas o hasta que no quede nada. El informe final es el de la última ronda:

```bash
uv run studio narration tts --model qwen-0.6b --file guiones/*.json --evaluate --retries 3
```

En los reintentos solo se vuelven a transcribir los párrafos regenerados. Con los 22 guiones de prueba y `--retries 4`, las rondas regeneraron 40 → 15 → 8 → 5 párrafos y terminaron con 18 de 22 guiones sin errores.

Necesita el comando `whisper` en el PATH (`pip install openai-whisper`). Los párrafos y sus transcripciones quedan en `<carpeta de salida>/whisper/<guion>/<n>.wav` y `.json`.

### Cómo funciona

1. El texto se corta en cada línea en blanco, en cada `[pausa N]`, en cada `[estilo:]` y en cada `[emocion:]`. Cada tramo se divide en bloques de hasta ~300 letras, cortando en el final de cada oración.
2. Cada bloque recibe lo que su motor entiende: referencia, estilo, emoción y gestos traducidos (`TRADUCCION` en [server/src/content_studio/narration/text/traducir.py](../../src/content_studio/narration/text/traducir.py)). Lo que un motor no soporta se quita y el script avisa.
3. **Qwen** genera varios bloques a la vez (el *lote*), agrupando los de la misma referencia. El lote automático mide la VRAM libre y calcula cuántos entran (~1.15 GiB el primero y ~1.3 GiB cada uno extra, con un máximo de 4). Los demás motores generan de a un bloque.
4. Recorta el silencio que el modelo deja en los bordes de cada bloque (~0.5 s por lado) y une los bloques con silencio: 0.25 s entre bloques, 0.6 s en una línea en blanco y N s en `[pausa N]`. Cada bloque va a la velocidad de su estilo, con `ffmpeg atempo`, que no altera el tono.
5. Con `--master voz`, masteriza: pasa-altos de 70 Hz y loudness lineal de dos pasadas hacia `--lufs`, verificado después con `ebur128`. Si el pico real no deja llegar al objetivo con ganancia lineal, la toma queda como normalización dinámica: se avisa y `master.tipo` lo registra.

### Formato del guion

Texto plano, con tildes y con los números en letras. **Las etiquetas como `[pause]` o `<break>` se leen en voz alta** (el script avisa si encuentra alguna). Las pausas cortas se controlan con la puntuación. Para las largas, usa una línea en blanco (0.6 s) o `[pausa 1.5]`. Las **reglas obligatorias** de todo guion y las pausas medidas por signo están en **[docs/formato-guion.md](docs/formato-guion.md#reglas-obligatorias)**.

---

## 4. Estilos

A diferencia de la API TTS de Gemini, ninguno de estos modelos entiende una instrucción de estilo en texto. **El estilo sale sobre todo de la referencia grabada en ese tono**; los parámetros solo lo ajustan ([styles.py](../../src/content_studio/narration/styles.py), `ESTILOS`).

| Estilo | Intención | Velocidad | temperature | exaggeration* | cfg_weight* |
|---|---|---|---|---|---|
| friendly | Cercano y tranquilo; ritmo ágil, como una conversación | 1.05 | 0.8 | 0.6 | 0.4 |
| soft | Sereno y cálido; ritmo medio, frases limpias | 1.00 | 0.7 | 0.4 | 0.5 |
| expert | Claro y seguro, como quien le explica a un colega; ritmo medio | 1.00 | 0.7 | 0.5 | 0.5 |
| clear | Preciso y sereno; articulación nítida, ritmo medio | 0.97 | 0.6 | 0.35 | 0.6 |
| steady | Parejo y profesional, sin énfasis exagerados; ritmo ágil | 1.05 | 0.6 | 0.3 | 0.5 |
| neutral | Referencia neutra de control | 1.00 | 0.7 | 0.5 | 0.5 |
| energetic | Enérgico y animado; también para `happy` y `urgent` | 1.00 | 0.8 | 0.7 | 0.3 |
| dramatic | Tenso y dramático; también para `fear` | 1.00 | 0.7 | 0.6 | 0.3 |
| sad | Lento y melancólico | 1.00 | 0.7 | 0.4 | 0.5 |
| intimate | Íntimo y suave; también para `whisper` en Qwen y OmniVoice | 1.00 | 0.7 | 0.4 | 0.5 |
| whisper | Susurrado | 1.00 | 0.7 | 0.3 | 0.5 |
| neutral-en | Neutro en inglés (`--language en`) | 1.00 | 0.7 | 0.5 | 0.5 |

\* Solo se aplican en Chatterbox (las emociones de Chatterbox los ajustan por intensidad). `temperature` aplica a los dos Qwen y a Chatterbox. Los valores de los estilos nuevos son iniciales: ajústalos tras grabar.

---

## 5. Grabar las referencias

Todo lo necesario para grabar está en **[docs/scripts/](docs/scripts/README.md)**:

- La guía general: el kit de **12 clips de 8–12 s** grabados en una sola sesión (5 estilos actuales, `neutral`, `energetic`, `dramatic`, `sad`, `intimate`, `neutral-en` y la neutral de control), equipo, técnica, reglas del español neutro, cómo convertir y verificar con ffmpeg, y el checklist.
- Un guion por clip, con actitud, versión marcada (pausas, énfasis y entonación), indicaciones frase por frase, palabras difíciles y el texto exacto. Más 6 clips de emoción opcionales para IndexTTS 2.5, que van en `reference/emotions/`.

Para grabar, abre **Mis voces**, elige el perfil y pulsa **Grabar**. El asistente sigue el kit de la guía en su orden: el guion de cada clip en el teleprompter, el reloj contra la duración objetivo (dentro del rango o fuera de él) y el medidor de nivel. Antes de empezar, «Probar sala» mide el ruido de fondo durante 5 s. Cada toma se sube como WAV y el chequeo automático le da su veredicto (bordes, duración, pico, ruido y texto) antes de que elijas; «Repetir» graba otra toma del mismo estilo y «Siguiente estilo» pasa al siguiente.

Las tomas se guardan en la carpeta de su perfil, `reference/<perfil>/takes/`, y no se versionan. Si el micrófono no graba a 48 kHz, la toma se convierte al subirla, y el chequeo lo anota. Los clips de emoción de IndexTTS van aparte, en `reference/emotions/`, como dice la guía.

Cada perfil guarda su referencia por estilo en `server/data/narration/reference/<perfil>/`: `<estilo>.wav` es el audio y `<estilo>.txt` el texto exacto. Los `.wav` no se versionan (`.gitignore`).

Para narrar con tu voz, `studio narration tts --profile <perfil>` usa las referencias de esa carpeta. Sin `--profile` vale `default` («Mi voz»), el perfil que se migró de `reference/`. Por qué 8–12 s y qué copia cada motor de la referencia: [docs/research/voicestudio-narracion/11](../../../docs/research/voicestudio-narracion/11-audio-de-referencia.md).

### 5.1 Voces libres del catálogo (`--voice`)

Para narrar sin grabarse, `narration voices` arma voces a partir de fuentes con licencia de uso comercial: **CC0 o dominio público** (lectores de LibriVox y donaciones de voz de Kyutai, estas últimas con consentimiento explícito para clonar) y licencias que **piden mención** (ver abajo). El catálogo y su procedencia (URL, tramo, transcripción, licencia y consentimiento) están en [voices/catalog.json](voices/catalog.json). Por qué estas fuentes, qué se descartó y cómo se midió: [docs/research/voces-libres-clonacion/](../../../docs/research/voces-libres-clonacion/README.md).

```bash
uv run studio narration voices --list                    # catálogo, licencia y estado de cada voz
uv run studio narration voices --build yesid           # una voz (~5 min en la 4060)
uv run studio narration voices --build all           # todo el catálogo
uv run studio narration tts --model cosyvoice3 --voice yesid --text "..."
```

Cómo se construye una voz (corre en el venv de CosyVoice 3):

1. Baja la fuente (caché en `voices/.fuentes/`), recorta el tramo del catálogo y lo normaliza como una grabación propia (−18 LUFS, pico real ≤ −3 dBTP). Ese clip real es el estilo `neutral`.
2. Genera los otros 11 estilos con CosyVoice 3, leyendo el texto del kit (`reference/<estilo>.txt`, o su versión en inglés):
   - los estilos con instrucción (`sad`, `energetic`, `dramatic`…) usan `instruct2`;
   - `neutral-en` de una voz en español usa zero-shot, porque `cross_lingual` pierde la voz. En una voz inglesa, `neutral-en` es la base.
3. Aprueba cada clip con estos criterios: similitud de hablante con la base ≥ 0.93 (WavLM-SV), WER ≤ 0.15 (whisper `large-v3-turbo`), 5–15 s, −20 a −16 LUFS, pico real ≤ −3 dBTP y sin pausas internas de 1 s o más. Si un clip no aprueba, lo regenera con otra semilla, hasta 3 rondas.
4. Escribe `voices/<voz>/aprobacion.json`. **Una voz entra en `--voice` solo si aprueba los 12 estilos.** `uv run studio narration voices --list` muestra las demás con su estado.

**Voces que piden mención.** Además de las CC0 o de dominio público, el catálogo tiene voces con licencias que exigen **mención**: CC BY (VCTK, Alba MacKenna), CC BY-SA (OpenSLR: Colombia, Perú y Venezuela) y Jenny (Dioco). "Mención" quiere decir **atribución**: puedes usar la voz, incluso con fines comerciales, si al publicar das crédito a su autor (quién es, de dónde sale, con qué licencia y que la usaste como referencia para una voz sintética). El texto exacto está en `atribucion` del catálogo. `narration tts --voice` lo imprime como "MENCIÓN OBLIGATORIA" y lo guarda en el `.json` de la toma (`voces[].mencion`). Pégalo en la descripción del video. Las BY-SA muestran además un aviso de "compartir igual". Detalle en [docs/research/voces-libres-clonacion/12](../../../docs/research/voces-libres-clonacion/12-voces-con-mencion.md).

El acento y si cada estilo "suena" a lo que dice **no se miden**: escucha `voices/<voz>/*.wav` antes de usar una voz en un video. Las voces de LibriVox no tienen consentimiento para clonar. Para uso comercial, mira [docs/research/voces-libres-clonacion/02](../../../docs/research/voces-libres-clonacion/02-derechos-copyright-y-voz.md).

---

## 6. Rendimiento

### 6.1 Motores de octubre (Qwen y Chatterbox)

**Equipo**: RTX 4060 Laptop 8 GB (compute 8.9), WSL2, bf16, sin flash-attn. **Prueba**: guion de 6 párrafos (~145 palabras, ~47 s de audio), referencia de 11.5 s y estilo `expert`. **Velocidad** = segundos de audio generados por segundo de reloj, **incluyendo la carga del modelo**: más de 1× es más rápido que el tiempo real. **VRAM** = pico de PyTorch (`max_memory_reserved`), sin contar lo que usan otras apps.

| Modelo | Lote | Velocidad | 1 min de audio tarda | Pico VRAM |
|---|---|---|---|---|
| qwen-0.6b | 1 | 0.57× | ~1 min 45 s | 3.20 GiB |
| qwen-0.6b | 3 (auto, con ~2.8 GB ocupados) | 1.07× | ~56 s | 5.70 GiB |
| qwen-0.6b | 4 | **1.47×** | ~41 s | 7.02 GiB |
| qwen-1.7b | 1 | 0.60× | ~1 min 40 s | 5.11 GiB |
| qwen-1.7b | 2 (auto) | 0.86× | ~1 min 10 s | 6.46 GiB |
| chatterbox | 1 (no admite lote) | 1.01× | ~59 s | 4.29 GiB |

**Solo generación** (sin carga del modelo; 4 frases cortas, ~23 s de audio):

| Modelo | De a una frase | Lote de 4 | VRAM de pesos | Carga del modelo |
|---|---|---|---|---|
| qwen-0.6b | 0.50× | 1.71× (5.6 GiB) | 2.06 GiB | 6–7 s |
| qwen-1.7b | 0.53× | 1.75× (7.5 GiB) | 3.95 GiB | 6–16 s |

**Conclusiones**

- De a una frase, los dos Qwen generan **más lento que el tiempo real** y a la misma velocidad. La GPU queda al ~35 % de uso (~35 W): el límite es la generación token a token, no el cálculo. Por eso **el lote es lo que más acelera** (~3×).
- **La VRAM libre es el límite real.** Windows y otras apps ocupan entre 0.1 y 3.3 GB según lo que esté abierto. Si el modelo se pasa de la VRAM, el driver pasa memoria a la RAM compartida y todo se vuelve **~4× más lento**: una corrida del 1.7B bajó a 0.14×. El lote automático existe para evitar eso.
- En **calidad/velocidad**, conviene usar `qwen-0.6b` para iterar y `qwen-1.7b` para el render final, cerrando antes el navegador y otras apps que usen la GPU.
- **Calidad verificada con Whisper**: todas las salidas, con y sin lote, tienen la misma cantidad de palabras que el guion (150), sin cortes ni repeticiones. La cobertura del vocabulario fue de ~93 % con Whisper base y de 96–99 % con Whisper small. El faltante es sobre todo un nombre de marca poco común, que Whisper transcribe con otra ortografía.
- **Segunda ronda (2026-10-04)**: confirmó la tabla con un margen de ±10 %. qwen-0.6b dio 0.65× / 1.19× (auto, lote 3) / 1.60× (lote 4); qwen-1.7b, 0.62× / 0.92× (auto, lote 2); chatterbox, 1.09×. Los picos de VRAM coinciden con la tabla con ±0.1 GiB de diferencia. También se comprobó lo siguiente: la falta de referencia corta con `No existe la referencia`; la falta de `.txt` muestra el aviso y genera igual; el estilo `friendly` (×1.05) acorta el audio en la proporción esperada (46.8 s → 44.6 s); y los doctests pasan.
- **Ojo con el lote automático en WSL**: se calcula con `torch.cuda.mem_get_info()`, que **no coincide con nvidia-smi**. En una medición sin nada del proyecto corriendo, torch dio 6.93 GiB libres y nvidia-smi 3.9 GB. En la segunda ronda, con 3.8 GB libres según nvidia-smi, el lote automático eligió 3 y el total de la GPU llegó a 7.9 de 8 GB sin desbordar. Si otra app de verdad está usando la GPU, el lote automático puede quedarse corto de margen: en ese caso, fuerza `--batch 1` o `--batch 2`.

### 6.2 Motores de noviembre (medido en dev)

Medido en `dev` con un párrafo de ~290 letras (un bloque), referencia de prueba `expert`, semilla 1 y `--master voz` (por defecto). **La GPU seguía compartida** con otra aplicación (~3.5 GB ocupados), así que las velocidades son un piso: repítelas con la GPU libre antes de decidir por velocidad.

| Motor | Audio | Generación | Velocidad | Pico VRAM | Masterización |
|---|---|---|---|---|---|
| omnivoice | 14.6 s | 7.7 s | 1.89× | 5.34 GiB | −16.0 LUFS, −1.6 dBTP |
| voxcpm2 | 13.9 s | 28.6 s | 0.49× | 6.04 GiB | −16.1 LUFS, −1.5 dBTP |
| indextts | 20.2 s | 41.0 s | 0.49× | 6.02 GiB | −16.0 LUFS, −1.5 dBTP |
| cosyvoice3 | 14.9 s | 25.2 s | 0.59× | 4.04 GiB | −16.0 LUFS, −1.5 dBTP |
| chatterbox | 14.0 s | 22.8 s | 0.61× | 3.95 GiB | −16.1 LUFS, −1.5 dBTP |
| qwen-0.6b | 14.5 s | 29.9 s | 0.48× | 3.20 GiB | −16.0 LUFS, −1.5 dBTP |

Los seis picos de VRAM quedan por debajo de 6.5 GiB. Las seis tomas de `c_tutorial` (criterio 1) también salieron entre −15.9 y −16.0 LUFS con pico de −1.5 dBTP. En casi todas, la normalización es dinámica: el pico real de estas voces no deja llegar a −16 LUFS con ganancia lineal (ver [§7](#7-problemas-conocidos)). La toma de OmniVoice fue la única que necesitó reajustar el techo (ver `master.techo_tp` en su `.json`).

---

## 7. Problemas conocidos

- **Nombres de marca o poco comunes** se pronuncian distinto según el modelo. Si uno suena mal, escríbelo en el texto como se dice (por ejemplo, "Shaomi" en vez de "Xiaomi").
- **Sin `.txt` de referencia**, Qwen usa solo la huella de la voz (`x_vector_only_mode`) y clona peor. OmniVoice y CosyVoice 3 **no generan** sin `.txt`: el script se detiene y lo dice.
- **Acento inglés en Qwen**: aparece sobre todo con referencias que no son nativas. Usa referencias grabadas en español neutro.
- **Masterización dinámica con −16 LUFS**: con las voces de prueba, el pico real impide la normalización lineal. El limitador baja el rango de loudness (en una toma de OmniVoice, de 3.5 a 2.7 LU) y el `.json` lo registra en `master.tipo`. Si prefieres el audio sin limitar, usa un objetivo más bajo: en la toma de prueba de OmniVoice, `--lufs -19` quedó lineal.
- **VoxCPM2 no tiene semilla propia**: la versión instalada no acepta `seed` en `generate`, así que `narration tts` fija el generador global. Es reproducible en la misma máquina con el mismo código; no está garantizado en GPU.
- **Bloques que terminan sin puntuación**: OmniVoice puede devolver un audio vacío si el bloque no termina en `.`, `?` o `!`, por ejemplo cuando un `[estilo:]` corta la oración. El script avisa y deja el aviso en el `.json`.
- **Licencias**: OmniVoice (CC-BY-NC) e IndexTTS 2.5 **no son comerciales**: el script avisa en cada corrida. Qwen, Chatterbox, VoxCPM2 y CosyVoice 3 permiten uso comercial según su licencia. Clona solo voces con permiso de su dueño.
- **GPU compartida**: si otra aplicación usa la GPU, el lote automático y los tiempos cambian (ver [§6](#6-rendimiento)). Cierra antes las apps que usen la GPU.
- **Validación con tu voz pendiente**: los motores de noviembre se probaron con la referencia de prueba. Falta repetir el banco con tus grabaciones (spec §11.3) para fijar el motor por defecto de cada tipo de video.

## Fuentes

- [Qwen3-TTS (GitHub)](https://github.com/QwenLM/Qwen3-TTS) · [acento inglés en español #230](https://github.com/QwenLM/Qwen3-TTS/discussions/230) · [voces en español #300](https://github.com/QwenLM/Qwen3-TTS/discussions/300) · [review 2026](https://aitoolanalysis.com/qwen3-tts-review/)
- [Chatterbox (GitHub)](https://github.com/resemble-ai/chatterbox) · [review 2026](https://oakgen.ai/blog/chatterbox-tts-open-source-review) · [docs Clore](https://docs.clore.ai/guides/audio-and-voice/chatterbox-tts)
- Comparativas: [BentoML](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models) · [Pinggy](https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/) · [LocalAIMaster](https://localaimaster.com/blog/best-local-tts-models)
- Voces libres para clonar (fuentes CC0 y de dominio público, derechos, pruebas y catálogo): [docs/research/voces-libres-clonacion/](../../../docs/research/voces-libres-clonacion/README.md)
- Investigación de los motores de noviembre y especificación de la implementación: [docs/research/voicestudio-narracion/](../../../docs/research/voicestudio-narracion/README.md) · la spec eliminada al implementarse, en el historial de git (desviaciones en su §15)

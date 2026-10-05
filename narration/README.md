# narration/ — Narración TTS local con clonación de voz

Genera narración en **español neutro latinoamericano** clonando una voz de referencia, 100 % local en una **RTX 4060 Laptop (8 GB VRAM)**. Sin APIs ni costo por uso.

```
narration/
├── README.md            este documento
├── tts.py               script único (CLI)
├── docs/
│   ├── formato-guion.md cómo escribir el texto a narrar: pausas, entonación, pronunciación
│   └── guiones/         cómo grabar las referencias de voz: un guion por estilo
├── voz/                 referencias de voz: <estilo>.wav + <estilo>.txt
│   └── prueba/          referencia de prueba (experta.wav + .txt) mientras no grabes las tuyas
├── .venv-qwen/          venv de Qwen3-TTS        (gitignoreado)
└── .venv-chatterbox/    venv de Chatterbox V3    (gitignoreado)
```

Salidas en `out/narration/` de la raíz (gitignoreado), o donde indique `--salida`. Logs de corridas largas en `logs/`.

**Todavía no hay referencias grabadas** en `voz/<estilo>.wav`: hasta que las grabes (ver [docs/guiones/](docs/guiones/README.md)), agrega `--ref narration/voz/prueba/experta.wav`.

---

## 1. Modelos elegidos (investigación, oct-2026)

Filtro aplicado: modelos abiertos que **soportan español**, que **entran en ~6.9 GiB de VRAM libre** y que **clonan voz** (el español neutro se consigue con una referencia neutra; ningún modelo trae un "neutro" de fábrica).

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

**Descartados** (ver la investigación completa en el historial): VoxCPM2 (justo de VRAM y casi sin testimonios en español), Voxtral TTS (≥10 GB), Higgs Audio v3 (no comercial y lento en 8 GB), F5-TTS, XTTS v2 y Fish S1-mini (licencias no comerciales), Kokoro (acento inglés, no clona), Dia, IndexTTS2, Orpheus y Breeze TTS 2 (sin español).

En este proyecto, **Qwen 0.6B y 1.7B dieron el mejor resultado** al escucharlos.

---

## 2. Instalación

Cada modelo necesita su propio venv porque fijan versiones de `transformers` incompatibles (Qwen 4.57.3, Chatterbox 5.2.0). Chatterbox se instala desde GitHub porque la versión de PyPI (0.1.7) no trae V3.

```bash
uv venv -p 3.12 narration/.venv-qwen
VIRTUAL_ENV=narration/.venv-qwen uv pip install qwen-tts soundfile

uv venv -p 3.12 narration/.venv-chatterbox
VIRTUAL_ENV=narration/.venv-chatterbox uv pip install soundfile \
  "chatterbox-tts @ git+https://github.com/resemble-ai/chatterbox"
```

Los pesos se bajan solos a `~/.cache/huggingface` la primera vez (Qwen 1.7B ≈ 4 GB, 0.6B ≈ 2 GB). También se necesita `ffmpeg` en el PATH.

---

## 3. Uso

El script se re-ejecuta solo con el venv que corresponde, así que se puede lanzar con cualquier `python`:

```bash
# Texto directo, referencia por defecto (narration/voz/<estilo>.wav)
python narration/tts.py --modelo qwen-0.6b --estilo amistosa \
  --texto "Hola, bienvenidos al canal. Hoy te muestro cómo editar un video en un minuto."

# Guion desde archivo, modelo grande, salida con nombre
python narration/tts.py --modelo qwen-1.7b --estilo experta \
  --archivo guion.txt --salida out/narration/guion-experta.wav

# Con la referencia de prueba (mientras no haya grabaciones propias)
python narration/tts.py --modelo qwen-0.6b --ref narration/voz/prueba/experta.wav \
  --texto "Hola, esto es una prueba."

# Referencia puntual (un .wav con su .txt al lado) y Chatterbox
python narration/tts.py --modelo chatterbox --ref narration/voz/clara.wav \
  --estilo clara --archivo guion.txt

# Varios guiones JSON en una corrida (estilo e id salen de cada JSON)
python narration/tts.py --modelo qwen-0.6b --archivo guiones/*.json --salida out/narration/organic

# Forzar el tamaño de lote (por defecto se calcula según la VRAM libre)
python narration/tts.py --modelo qwen-0.6b --lote 4 --archivo guion.txt
```

Por cada guion imprime la duración, el lote usado, la velocidad y el pico de VRAM. El tiempo del primer guion incluye la carga del modelo:

```
out/narration/qwen-0.6b-experta.wav (47.7 s, qwen-0.6b, experta, lote 3) | generación 44.6 s, 1.07x tiempo real | pico VRAM 5.70 GiB
```

### Flags

| Flag | Valores | Por defecto | Qué hace |
|---|---|---|---|
| `--modelo` | `qwen-1.7b`, `qwen-0.6b`, `chatterbox` | obligatorio | Modelo a usar |
| `--ref` | `.wav` o carpeta | `narration/voz` | Con una carpeta usa `<estilo>.wav`. La transcripción va en el `.txt` homónimo |
| `--estilo` | `amistosa`, `suave`, `experta`, `clara`, `estable` | el `estilo` del JSON, o `experta` | Elige la referencia y los parámetros |
| `--texto` | texto | uno de los dos | Lo que se narra |
| `--archivo` | uno o varios `.txt` o `.json` | uno de los dos | Guiones a narrar. Con varios, el modelo se carga una sola vez. Formato JSON en [docs/formato-guion.md](docs/formato-guion.md#guiones-en-json) |
| `--salida` | ruta | `out/narration/` | Con un solo guion, el `.wav`; con varios, la carpeta. Nombre por defecto: `<id>-<modelo>.wav` (JSON) o `<modelo>-<estilo>.wav` |
| `--lote` | entero | automático | Frases por pasada en Qwen: más rápido, pero usa más VRAM |

### Cómo funciona

1. El texto se corta en cada línea en blanco y en cada marca `[pausa N]`. Cada tramo se divide en bloques de hasta ~300 letras, cortando en el final de cada oración.
2. **Qwen** genera varios bloques a la vez (el *lote*). El lote automático mide la VRAM libre y calcula cuántos entran (~1.15 GiB el primero y ~1.3 GiB cada uno extra, con un máximo de 4). **Chatterbox** no admite lotes y genera de a uno.
3. Recorta el silencio que el modelo deja en los bordes de cada bloque (~0.5 s por lado) y une los bloques con silencio: 0.25 s entre bloques, 0.6 s en una línea en blanco y N s en `[pausa N]`. Después aplica la velocidad del estilo con `ffmpeg atempo`, que no altera el tono.

### Formato del guion

Texto plano, con tildes y con los números en letras. **Las etiquetas como `[pause]` o `<break>` se leen en voz alta** (el script avisa si encuentra alguna). Las pausas cortas se controlan con la puntuación. Para las largas, usa una línea en blanco (0.6 s) o `[pausa 1.5]`. Las **reglas obligatorias** de todo guion y las pausas medidas por signo están en **[docs/formato-guion.md](docs/formato-guion.md#reglas-obligatorias)**.

---

## 4. Estilos

A diferencia de la API TTS de Gemini, ninguno de estos modelos entiende una instrucción de estilo en texto. **El estilo sale sobre todo de la referencia grabada en ese tono**; los parámetros solo lo ajustan ([tts.py](tts.py), `ESTILOS`).

| Estilo | Intención | Velocidad | temperature | exaggeration* | cfg_weight* |
|---|---|---|---|---|---|
| amistosa | Cercano y tranquilo; ritmo ágil, como una conversación | 1.05 | 0.8 | 0.6 | 0.4 |
| suave | Sereno y cálido; ritmo medio, frases limpias | 1.00 | 0.7 | 0.4 | 0.5 |
| experta | Claro y seguro, como quien le explica a un colega; ritmo medio | 1.00 | 0.7 | 0.5 | 0.5 |
| clara | Preciso y sereno; articulación nítida, ritmo medio | 0.97 | 0.6 | 0.35 | 0.6 |
| estable | Parejo y profesional, sin énfasis exagerados; ritmo ágil | 1.05 | 0.6 | 0.3 | 0.5 |

\* Solo se aplican en Chatterbox. `temperature` aplica a los dos modelos.

---

## 5. Grabar las referencias

Todo lo necesario para grabar está en **[docs/guiones/](docs/guiones/README.md)**:

- La guía general: equipo, reglas del español neutro, cómo grabar, convertir con ffmpeg y probar la referencia, y el checklist.
- Un guion por estilo, con actitud, versión marcada (pausas, énfasis y entonación), indicaciones frase por frase, palabras difíciles y el texto exacto.

Cada grabación va en `narration/voz/<estilo>.wav` y debe decir exactamente lo de `narration/voz/<estilo>.txt`.

---

## 6. Rendimiento medido

**Equipo**: RTX 4060 Laptop 8 GB (compute 8.9), WSL2, bf16, sin flash-attn. **Prueba**: guion de 6 párrafos (~145 palabras, ~47 s de audio), referencia de 11.5 s y estilo `experta`. **Velocidad** = segundos de audio generados por segundo de reloj, **incluyendo la carga del modelo**: más de 1× es más rápido que el tiempo real. **VRAM** = pico de PyTorch (`max_memory_reserved`), sin contar lo que usan otras apps.

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
- **Segunda ronda (2026-10-04)**: confirmó la tabla con un margen de ±10 %. qwen-0.6b dio 0.65× / 1.19× (auto, lote 3) / 1.60× (lote 4); qwen-1.7b, 0.62× / 0.92× (auto, lote 2); chatterbox, 1.09×. Los picos de VRAM coinciden con la tabla con ±0.1 GiB de diferencia. También se comprobó lo siguiente: la falta de referencia corta con `No existe la referencia`; la falta de `.txt` muestra el aviso y genera igual; el estilo `amistosa` (×1.05) acorta el audio en la proporción esperada (46.8 s → 44.6 s); y los doctests pasan.
- **Ojo con el lote automático en WSL**: se calcula con `torch.cuda.mem_get_info()`, que **no coincide con nvidia-smi**. En una medición sin nada del proyecto corriendo, torch dio 6.93 GiB libres y nvidia-smi 3.9 GB. En la segunda ronda, con 3.8 GB libres según nvidia-smi, el lote automático eligió 3 y el total de la GPU llegó a 7.9 de 8 GB sin desbordar. Si otra app de verdad está usando la GPU, el lote automático puede quedarse corto de margen: en ese caso, fuerza `--lote 1` o `--lote 2`.

Para medir de nuevo, cualquier corrida imprime velocidad y pico de VRAM. Para ver el uso total de la GPU: `nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv -l 1`.

---

## 7. Problemas conocidos

- **Nombres de marca o poco comunes** se pronuncian distinto según el modelo. Si uno suena mal, escríbelo en el texto como se dice (por ejemplo, "Shaomi" en vez de "Xiaomi").
- **Sin `.txt` de referencia**, Qwen usa solo la huella de la voz (`x_vector_only_mode`) y clona peor. El script avisa.
- **Acento inglés en Qwen**: aparece sobre todo con referencias que no son nativas. Usa referencias grabadas en español neutro.
- **Licencias**: las dos permiten uso comercial, así que sirven para videos de ventas. Aun así, clona solo voces con permiso de su dueño.

## Fuentes

- [Qwen3-TTS (GitHub)](https://github.com/QwenLM/Qwen3-TTS) · [acento inglés en español #230](https://github.com/QwenLM/Qwen3-TTS/discussions/230) · [voces en español #300](https://github.com/QwenLM/Qwen3-TTS/discussions/300) · [review 2026](https://aitoolanalysis.com/qwen3-tts-review/)
- [Chatterbox (GitHub)](https://github.com/resemble-ai/chatterbox) · [review 2026](https://oakgen.ai/blog/chatterbox-tts-open-source-review) · [docs Clore](https://docs.clore.ai/guides/audio-and-voice/chatterbox-tts)
- Comparativas: [BentoML](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models) · [Pinggy](https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/) · [LocalAIMaster](https://localaimaster.com/blog/best-local-tts-models)

# server/data/music/ — música instrumental local (GPU 8 GB)

Genera música de fondo **instrumental** para los videos, en local y sin costo: lofi, corporate, ambient o cualquier estilo descrito en texto libre. Hay dos modelos: **ACE-Step 1.5** (el recomendado) y **HeartMuLa 3B**.

La investigación de los modelos (cuáles se eligieron y cuáles se descartaron, y por qué) está en [INVESTIGACION.md](INVESTIGACION.md).

## Uso

Desde la raíz del repo, con cualquier Python: el script se relanza solo en el venv que corresponde.

```bash
# Un preset (tonalidad, BPM y compás ya definidos)
python cli.py music --model acestep --style lofi-chill --duration 60

# Varios presets para escucharlos y comparar (el modelo se carga una sola vez)
python cli.py music --model acestep --duration 30 \
  --style lofi-chill corporate future-bass deep-house ambient

# Texto libre: exige --key y --bpm (--time-signature es opcional, 4/4 por defecto)
python cli.py music --model acestep --duration 30 --key "E Minor" --bpm 105 \
  --style "synthwave, retro 80s, driving arpeggios"

# Un preset con otra tonalidad o tempo (los flags pisan los valores del preset)
python cli.py music --model acestep --style lofi-jazz --key "G Major" --bpm 90

# Sin el planificador LM: ~3x más rápido (ver "Qué hace --no-lm")
python cli.py music --model acestep --style ambient --no-lm

# Otra carpeta de salida
python cli.py music --model acestep --style corporate --folder out/mi-proyecto

# HeartMuLa (lento; ignora --key, --bpm y --time-signature)
python cli.py music --model heartmula --style lofi-rain --duration 30
```

**Salida**: `out/music/<modelo>-<estilo>.wav` (en la raíz del repo; 48 kHz, estéreo) con el **silencio final ya recortado**. Cambia la carpeta con `--folder`. Al terminar imprime cuántos segundos quedaron, la tonalidad y el BPM:

```
out/music/acestep-lofi-jazz.wav (22.5 s tras recortar el silencio; D Minor, 85 BPM)
```

| Flag | Valor | Por defecto |
|:--|:--|:--|
| `--model` | `acestep` \| `heartmula` | obligatorio |
| `--style` | uno o más presets o textos libres | `lofi-chill` |
| `--duration` | segundos que se generan **antes** del recorte (ACE hasta 600, HeartMuLa hasta 240) | 60 |
| `--key` | tonalidad: `"C Major"`, `"A Minor"`, `"F# Minor"`… | la del preset (obligatoria con texto libre) |
| `--bpm` | tempo, de 30 a 300 | el del preset (obligatorio con texto libre) |
| `--time-signature` | `2`, `3`, `4` o `6` (2/4, 3/4, 4/4, 6/8) | el del preset, o `4` |
| `--no-lm` | solo ACE-Step | apagado |
| `--folder` | carpeta de salida | `out/music/` |
| `--variants` | pistas por estilo; con más de 1 los archivos son `<modelo>-<estilo>-v1.wav`, `-v2.wav`… (la melodía cambia en cada una) | 1 |
| `--evaluate` | solo ACE-Step: al final mide con demucs cuánta voz hay en cada pista (ver "Evaluar que no haya voz") | apagado |
| `--retries` | con `--evaluate`: rondas que regeneran solo las pistas con voz | 0 |

Si usas texto libre sin `--key` y `--bpm`, el script se detiene antes de cargar el modelo y muestra el mensaje: `"bossa nova" no es un preset: define --key y --bpm`. `--key`, `--bpm` y `--time-signature` se aplican a **todos** los estilos de esa corrida.

### Estilos predefinidos

| Preset | Descripción | Tonalidad | BPM | Compás |
|:--|:--|:--|:--|:--|
| `lofi-chill` | Rhodes, vinilo, boom bap suave | C Major | 80 | 4/4 |
| `lofi-jazz` | Acordes de jazz, trompeta con sordina, escobillas | D Minor | 85 | 4/4 |
| `lofi-rain` | Piano melancólico, ambiente de lluvia | E Minor | 72 | 4/4 |
| `lofi-study` | Guitarra suave, groove relajado, minimal | G Major | 78 | 4/4 |
| `lofi-night` | Pads de sintetizador, sub bajo, ciudad de noche | A Minor | 70 | 4/4 |
| `corporate` | Fondo tech optimista, piano eléctrico, plucks | C Major | 110 | 4/4 |
| `future-bass` | Supersaw suaves, sidechain leve, brillante | G Major | 100 | 4/4 |
| `deep-house` | Groove cálido, bajo redondo, elegante | A Minor | 120 | 4/4 |
| `ambient` | Pads que evolucionan, sin batería | D Major | 70 | 4/4 |

Las tonalidades son las que la guía oficial de ACE-Step considera estables: C, G, D, Am, Em y sus vecinas. Las tonalidades poco comunes "pueden ignorarse o desplazarse".

### Catálogo ampliado: 117 presets más

Definidos en [styles.py](../../src/content_studio/music/styles.py); la tabla completa con descripción, tono y BPM está en [ESTILOS.md](ESTILOS.md). Pensados como fondo para tutoriales, publicidad, demos y videos. Cada uno se generó a 30 s con ACE-Step y pasó `--evaluate` (ver más abajo). Se usan igual que los otros: `--style <nombre>`.

| Grupo | Presets |
|:--|:--|
| Tutoriales y explicativos | `tutorial-calm` `tutorial-tech` `tutorial-guitar` `explainer-animated` `explainer-minimal` `course-online` `step-by-step` `codigo` `documentary-soft` |
| Corporativo y publicidad | `corporate-inspiring` `corporate-minimal` `corporate-energetic` `corporate-startup` `corporate-trust` `corporate-innovation` `corporate-motivational` `ad-happy` `ad-premium` `ad-fashion` `ad-sports` `ad-food` `ad-launch` `ad-fintech` `ad-realestate` `ad-health` `ad-travel` `ad-car` |
| Demos y tecnología | `demo-product` `demo-saas` `demo-mobile-app` `demo-futuristic` `demo-ai` `demo-gadget` `demo-shop` `demo-dashboard` `demo-game` |
| Lofi | `lofi-cafe` `lofi-guitar` `lofi-sunset` `lofi-nostalgic` `lofi-bossa` `chillhop-focus` `lofi-piano` `vaporwave` |
| Ambient, foco y bienestar | `ambient-space` `ambient-piano` `ambient-cinematic` `ambient-forest` `ambient-ocean` `meditation` `yoga` `spa` `sleep` `deep-focus` `new-age` `ambient-dark` |
| Cinematográfico | `cinematic-emotional` `cinematic-hope` `trailer-tension` `cinematic-minimal` `documentary-nature` `heroic` `mystery` `suspense-tech` `sci-fi` `fantasy` `orchestra-warm` `piano-emotional` `strings-minimal` `neoclassical` |
| Acústico y folk | `acoustic-happy` `acoustic-warm` `folk-soft` `country-soft` `piano-pop` `ukulele-beach` `guitar-classical` `harp-celestial` `celtic` |
| Jazz, latino y del mundo | `jazz-cafe` `jazz-soft` `bossa-nova` `lounge` `swing-happy` `latin-soft` `cumbia-soft` `reggae-chill` `afrobeat-light` `tropical-house` |
| Electrónica y pop | `pop-bright` `synthwave` `retrowave-soft` `trap-soft` `drum-and-bass-light` `techno-minimal` `house-happy` `tech-house` `edm-energetic` `electropop` `downtempo` `chillwave` `future-garage` `chiptune-happy` `funk-soft` `disco` `boom-bap` `rnb-soft` `rock-motivational` `indie-pop` `post-rock-soft` |
| Usos concretos | `christmas-soft` `kids` `casual-game` `workout` `news` `cooking` `vlog-travel` |

**Cómo se probaron**: una pista de 30 s por preset, con LM. Pasa si no tiene voz (`--evaluate`, umbral −25 dB), dura al menos 20 s tras recortar el silencio y no es casi muda. Pasaron 117 de 119: ninguna salió corta ni silenciosa (20,6–30 s, mediana 26,8 s) y se descartaron 2 por voz (ver [INVESTIGACION.md](INVESTIGACION.md)). **Nadie las escuchó**: las métricas no dicen si suenan bien ni si el estilo se reconoce. Con una sola muestra por preset, el resultado es indicativo.

Presets limítrofes en voz (entre −25 y −32 dB, pasaron por poco): `demo-product`, `heroic`, `suspense-tech`, `ambient-ocean`, `tutorial-tech`, `sci-fi`, `pop-bright`, `demo-saas`. Si los vas a usar, genera con `--evaluate --retries 2`.

Bajo una narración, los que mejor acompañan son los de tutoriales y explicativos, `corporate-minimal`, `deep-house` y `ambient`.

Para agregar un preset, suma una entrada a `NUEVOS` en [styles.py](../../src/content_studio/music/styles.py): `nombre: (caption en inglés, tono, bpm[, compás])`. El script agrega `no vocals` al caption y deriva los tags de HeartMuLa. Pruébalo con `--evaluate` antes de confiar en él.

## Evaluar que no haya voz (`--evaluate`)

ACE-Step recibe `[Instrumental]`, pero a veces se le cuela una voz. `--evaluate` separa cada pista con **demucs** (`htdemucs`), mide el nivel del stem de voz respecto de la mezcla y marca como `VOZ` las que superan `VOZ_MAX_DB = -25` dB. Con `--retries N` regenera solo esas pistas (semilla nueva) hasta N rondas; si alguna sigue con voz, el script termina con error y las nombra.

```bash
python cli.py music --model acestep --duration 30 --variants 4 --evaluate --retries 2 \
  --folder out/music-variantes --style lofi-chill corporate ambient
```

```
  ok   acestep-lofi-chill-v1.wav: voz -39.3 dB respecto de la mezcla
  VOZ  acestep-lofi-chill-v2.wav: voz -4.9 dB respecto de la mezcla
```

- **Por qué demucs y no whisper**: whisper alucina frases sobre música instrumental (`"Outro Music"`, `"Let me know what you think about this video…"`) y marcó como "con voz" pistas que no la tenían. Sus métricas (`no_speech_prob`, `avg_logprob`) no separan la alucinación de la letra real.
- **Calibración del umbral**: pistas instrumentales de ACE-Step, entre −35 y −44 dB; una pista cantada a propósito (letra y `vocal_language='en'`), −4,9 dB. Medido sobre pocas pistas: si aparece un falso positivo o negativo, ajusta `VOZ_MAX_DB`.
- demucs vive solo en `.venv-acestep` (instalado con `--no-deps` para no tocar torch), así que `--evaluate` no funciona con `--model heartmula`.
- Cada ronda recarga ACE-Step (~30 s) y carga demucs en la GPU tras liberar la VRAM del generador.

## Cómo funciona ACE-Step (y qué hace `--no-lm`)

ACE-Step 1.5 usa dos modelos en cadena (fuente: `models/ACE-Step-1.5/docs/en/Tutorial.md` e `INFERENCE.md`):

```
caption + metadatos → [LM 5 Hz, 0.6B] → plan semántico → [DiT turbo, 2B] → audio
```

- **El LM es el "planificador"** (un modelo de lenguaje de 0.6B). Hace tres cosas:
  1. **Completa los metadatos que faltan** (BPM, tonalidad, compás y duración) mediante razonamiento *chain-of-thought*. Si se los das, no los inventa: los usa como restricción al decodificar (`user_metadata`).
  2. **Reescribe y amplía el caption.**
  3. **Genera "códigos semánticos" a 5 Hz**, que contienen la melodía, la orquestación y la estructura. Esos códigos guían al DiT.
- **El DiT es el "ejecutor"**: un modelo de difusión que convierte el plan en audio en 8 pasos. Decide el timbre, la mezcla y los detalles.

**`--no-lm` apaga el planificador.** El DiT genera directamente a partir del caption y los metadatos (tonalidad, BPM y compás). En consecuencia:

- Es **~3× más rápido**: 12 s contra ~36 s en una pista de 20 s, porque se salta la generación de códigos, que es token a token.
- Ahorra **poca VRAM**: ~0,2 GB.
- **No hay plan de melodía ni de estructura**: el DiT improvisa sobre el caption. La guía oficial lo recomienda cuando "ya tienes los metadatos precisos" y quieres velocidad o control total. Recomienda dejar el LM activo para tener mejor estructura y variedad.
- La tonalidad y el BPM se respetan igual, porque ahora los definen los presets o los flags. En la verificación, `ambient --no-lm` dio D Major a 69,8 BPM, cuando se pidió D Major a 70 BPM.

En resumen: con el LM, la estructura es mejor y cada corrida da una melodía distinta en la misma tonalidad. Sin el LM, la generación es más rápida y más plana. Conviene usar `--no-lm` para iterar y el LM para la pista final.

## Rendimiento medido

Equipo: RTX 4060 Laptop, 8 GiB, WSL2. Medido el 2026-10-04 en dos rondas independientes y con los pesos ya descargados. Cada tiempo incluye la carga del modelo.

| | **ACE-Step 1.5 turbo** | **HeartMuLa 3B** |
|:--|:--|:--|
| 1 pista de 30 s | **43–51 s** | **283–296 s** |
| 1 pista de 60 s | **47–51 s** | 296–416 s. Pedí 60 s y entregó 12 s una vez y 42 s otra |
| 5 estilos de 30 s en una sola corrida | **103–121 s** (~15 s por cada pista extra) | no probado |
| 1 pista de 20 s con `--no-lm` | **12 s** (con LM: ~36 s) | — |
| Pico de VRAM del proceso (nvidia-smi menos la base) | **~6,0 GB** (~5,8 GB con `--no-lm`) | ~7,1 GB, la GPU llena |
| Pico de memoria que reporta torch | 5,96 GB | **12,67 GB** en el LM y 6,20 GB en el codec |
| ¿Entra en 8 GB? | ✅ Sí, si hay ~6,5 GB libres | ⚠️ **No.** Corre porque el driver de Windows/WSL desborda a la RAM compartida, y por eso es lento |
| Tonalidad, BPM y compás | ✅ Se respetan (verificado con análisis de croma y tempo) | ❌ No tiene esos parámetros |
| Carácter lofi (espectrograma) | ✅ Batería regular y agudos recortados | Mezcla densa y brillante, menos lofi |
| Pesos en disco | 11 GB | 21 GB |
| venv | 7,7 GB | 3,3 GB |

**Conclusión: usa ACE-Step.** Es entre 5 y 10 veces más rápido, entra en la GPU, respeta la tonalidad y el tempo, y suena más lofi. HeartMuLa queda solo para comparar.

**Verificación de tonalidad y tempo** (análisis de croma Krumhansl y `beat_track` de librosa):

| Pista | Pedido | Estimado en el audio |
|:--|:--|:--|
| `lofi-chill` | C Major, 80 | A Minor, la relativa de C Major (mismas notas), con C Major como segunda opción; 161,5 = 2 × 80 |
| `lofi-jazz` | D Minor, 85 | D Minor; 172 = 2 × 85 |
| texto libre `--key "E Minor" --bpm 105` | E Minor, 105 | E Minor; 103 |
| `ambient --no-lm` | D Major, 70 | D Major; 69,8 |

Es normal que el detector de tempo marque el doble del BPM.

## El silencio final se recorta solo

ACE-Step genera exactamente los segundos pedidos, pero suele **terminar la música antes** y rellenar el resto con silencio. Medido por debajo de −50 dB, quedaron 0,8 s de silencio en pistas de 60 s, entre 0 y 5 s en pistas de 30 s y 10–11 s en pistas de 20 s. El script recorta esa cola con ffmpeg (`areverse,silenceremove,areverse`, umbral `SILENCIO_DB = -50`), así que **la pista final puede durar menos que `--duration`**. Por ejemplo, `lofi-jazz` pedido a 30 s quedó en 22,5 s.

Por eso conviene pedir **30 s o más**, con margen sobre lo que necesitas.

## Cómo usarlo en un video (guía para la IA)

Flujo recomendado:

1. **Mide la narración primero** (`ffprobe` sobre el `.wav` de `out/narration/`). Pide la música con `--duration` = narración + 10 s (**mínimo 30**) y revisa los segundos que imprime el script: tienen que cubrir la narración.
2. **Genera 3–5 presets en una sola corrida** con `--duration 30` (o `--no-lm` para ir más rápido) para que el usuario elija de oído. Después regenera el elegido con la duración final y con el LM activo. La tonalidad y el BPM se mantienen; la melodía cambia en cada corrida.
3. **No anuncies que suena bien sin escucharlo.** Verifica la duración, el volumen y el espectrograma (ver "Cómo verificar"). El gusto lo decide el usuario: entrégale las rutas.
4. **Mezcla bajo la voz** con ducking: la música baja sola cuando hay narración. El comando está probado con una narración de Qwen y una pista de ACE-Step, y da una mezcla de −20 dB de media con picos de −4 dB:

   ```bash
   ffmpeg -y -i out/narration/narracion.wav -i out/music/acestep-lofi-chill.wav -filter_complex \
     "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit[v][sc];\
      [1:a]volume=0.25[m];[m][sc]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];\
      [v][duck]amix=inputs=2:duration=first:normalize=0[out]" \
     -map "[out]" out/mezcla.wav
   ```

   - La narración sale mono a 24 kHz y la música estéreo a 48 kHz. Por eso se usa `aformat`.
   - `volume=0.25` es el nivel base de la música. Súbelo a 0.35 para un fondo más presente o bájalo a 0.15 si tapa la voz.
   - `duration=first` corta la mezcla al largo de la narración. Si quieres una cola musical, agrega `apad=pad_dur=3` a la voz y `afade=t=out:st=<fin-2>:d=2` al final.

Tips para el prompt (texto libre de `--style`):

- Escríbelo **en inglés y con etiquetas separadas por comas**, siguiendo este orden: género, instrumentos, textura o producción, estado de ánimo y uso. Ejemplo: `"chillhop, nylon guitar, soft keys, vinyl crackle, warm, background music"`. Así están escritos los presets.
- **No pongas el tempo ni la tonalidad en el caption**: van en `--key` y `--bpm`. La guía oficial lo recomienda así y advierte que, si el caption contradice los metadatos (por ejemplo, "slow ballad" con 160 BPM), el modelo se confunde.
- Agrega `background`, `minimal` o `no drums` cuando la pista va bajo una narración. Una melodía muy cargada compite con la voz.
- Elige un BPM coherente con el género: lofi entre 70 y 90, corporate entre 100 y 120, house entre 118 y 126.

Detalles operativos:

- **El nombre de salida se sobrescribe**: `<modelo>-<estilo>.wav` no lleva fecha. Para guardar variantes, usa `--folder out/<proyecto>` o renombra el archivo antes de regenerarlo.
- **Primera corrida**: descarga ~11 GB (ACE-Step) o ~21 GB (HeartMuLa). Si se corta, vuelve a correrla.
- **Logs**: las corridas largas se lanzan en segundo plano y su salida se guarda en `logs/` de la raíz (por ejemplo, `logs/music-<fecha>.log`). HeartMuLa tarda ~5 min por pista.
- **Un modelo a la vez en la GPU**: no generes música mientras corre `narration tts`, porque los dos juntos no caben en 8 GB y el desborde a la RAM compartida hace todo ~4× más lento. Antes de lanzar, revisa la VRAM libre con `nvidia-smi --query-gpu=memory.free --format=csv`: ACE-Step necesita ~6,5 GB. Otros procesos, como el daemon `laya` de Synapse, pueden estar ocupando varios GB.
- El LM `acestep-5Hz-lm-1.7B` también está descargado en `checkpoints/`, pero no se usa: es el perfil de 8–16 GB y necesita vLLM.

## Instalación (desde cero)

Requisitos: `uv`, `git`, `ffmpeg` y una GPU NVIDIA. Los modelos y los venvs quedan dentro de `server/data/music/`; `models/` y `.venv-*` están gitignoreados.

```bash
cd music
git clone --depth 1 https://github.com/ACE-Step/ACE-Step-1.5.git models/ACE-Step-1.5
git clone --depth 1 https://github.com/HeartMuLa/heartlib.git models/heartlib

# ACE-Step (Python 3.12, torch 2.10 cu128)
(cd models/ACE-Step-1.5 && UV_PROJECT_ENVIRONMENT=../../.venv-acestep uv sync)

# HeartMuLa (Python 3.10). En Linux se resuelve datasets 2.14, que usa pa.PyExtensionType: pyarrow<21
uv venv -p 3.10 .venv-heartmula && VIRTUAL_ENV=.venv-heartmula uv pip install -e models/heartlib "pyarrow<21"
```

Los pesos se descargan solos en la primera corrida:
- ACE-Step → `models/ACE-Step-1.5/checkpoints/` (DiT turbo, VAE, Qwen3-Embedding, LMs).
- HeartMuLa → `models/heartmula-ckpt/` (HeartMuLaGen, HeartMuLa-oss-3B-happy-new-year, HeartCodec-oss-20260123).

Si se corta la descarga, vuelve a correr el script: reanuda donde quedó.

Para `--evaluate`, demucs en el venv de ACE-Step (sin dependencias, para no cambiar torch):

```bash
VIRTUAL_ENV=.venv-acestep uv pip install --no-deps demucs
VIRTUAL_ENV=.venv-acestep uv pip install julius einops lameenc openunmix dora-search
```

**En Windows** (PowerShell o Git Bash) los comandos son los mismos, salvo HeartMuLa: primero torch con CUDA desde el índice de PyTorch, porque desde PyPI llega la versión que solo usa CPU (y `--torch-backend` no sirve: busca `torchtune` solo en ese índice).

```bash
uv venv -p 3.10 .venv-heartmula
VIRTUAL_ENV=.venv-heartmula uv pip install torch==2.10.0 torchaudio==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cu128
VIRTUAL_ENV=.venv-heartmula uv pip install -e models/heartlib
```

Los venvs no se pueden mover de carpeta, porque guardan rutas absolutas. Si mueves `server/data/music/`, borra los `.venv-*` y vuelve a crearlos con los comandos de arriba (con la caché de uv tarda poco).

## Estructura

```
server/data/music/
├── README.md          # este archivo
├── INVESTIGACION.md   # modelos evaluados, descartes y fuentes
├── ESTILOS.md         # catálogo de presets
├── models/            # repos clonados y pesos (gitignoreado)
├── .venv-acestep/     # gitignoreado
└── .venv-heartmula/   # gitignoreado
```

El código está en `server/src/content_studio/music/` (parser, musica, estilos, evaluacion y `engines/`) y se lanza con `python cli.py music ...` o, directo, `PYTHONPATH=server/src python -m content_studio.music.musica ...`. Las salidas van a `out/music/` y los logs a `logs/`, ambos en la raíz del repo y gitignoreados.

## Cómo verificar un resultado

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 out/music/acestep-lofi-chill.wav   # duración
ffmpeg -i out/music/acestep-lofi-chill.wav -af volumedetect -f null - 2>&1 | grep volume       # volumen
ffmpeg -y -i out/music/acestep-lofi-chill.wav -lavfi showspectrumpic=s=800x300 out/spec.png    # espectrograma
```

El volumen medio sale entre −15 y −21 dB, con picos de −1 dB, porque ACE-Step lo normaliza. Para usarlo bajo la narración hay que bajarlo en la mezcla.

## Problemas conocidos

- **HeartMuLa no guarda el audio** (`TorchCodec is required` o `libnvrtc.so.13`): torchaudio 2.10 guarda mediante torchcodec, que no carga con este CUDA. El script ya lo resuelve guardando con `soundfile`. **No instales torchcodec** en `.venv-heartmula`.
- **HeartMuLa entrega menos duración de la pedida**: el modelo cierra la pista cuando quiere. El script repite secciones `[Instrumental]` (una cada ~20 s) para estirarla, pero no está garantizado.
- **ACE-Step con OOM**: cierra las apps que estén usando la GPU o usa `--no-lm`.

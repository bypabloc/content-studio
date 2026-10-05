# music/ — música instrumental local (GPU 8 GB)

Genera música de fondo **instrumental** para los videos, en local y sin costo: lofi, corporate, ambient o cualquier estilo descrito en texto libre. Hay dos modelos: **ACE-Step 1.5** (el recomendado) y **HeartMuLa 3B**.

La investigación de los modelos (cuáles se eligieron y cuáles se descartaron, y por qué) está en [INVESTIGACION.md](INVESTIGACION.md).

## Uso

Desde la raíz del repo, con cualquier Python: el script se relanza solo en el venv que corresponde.

```bash
# Un preset (tonalidad, BPM y compás ya definidos)
python music/musica.py --modelo acestep --estilo lofi-chill --duracion 60

# Varios presets para escucharlos y comparar (el modelo se carga una sola vez)
python music/musica.py --modelo acestep --duracion 30 \
  --estilo lofi-chill corporate future-bass deep-house ambient

# Texto libre: exige --tono y --bpm (--compas es opcional, 4/4 por defecto)
python music/musica.py --modelo acestep --duracion 30 --tono "E Minor" --bpm 105 \
  --estilo "synthwave, retro 80s, driving arpeggios"

# Un preset con otra tonalidad o tempo (los flags pisan los valores del preset)
python music/musica.py --modelo acestep --estilo lofi-jazz --tono "G Major" --bpm 90

# Sin el planificador LM: ~3x más rápido (ver "Qué hace --sin-lm")
python music/musica.py --modelo acestep --estilo ambient --sin-lm

# Otra carpeta de salida
python music/musica.py --modelo acestep --estilo corporate --carpeta out/mi-proyecto

# HeartMuLa (lento; ignora --tono, --bpm y --compas)
python music/musica.py --modelo heartmula --estilo lofi-lluvia --duracion 30
```

**Salida**: `out/music/<modelo>-<estilo>.wav` (en la raíz del repo; 48 kHz, estéreo) con el **silencio final ya recortado**. Cambia la carpeta con `--carpeta`. Al terminar imprime cuántos segundos quedaron, la tonalidad y el BPM:

```
out/music/acestep-lofi-jazz.wav (22.5 s tras recortar el silencio; D Minor, 85 BPM)
```

| Flag | Valor | Por defecto |
|:--|:--|:--|
| `--modelo` | `acestep` \| `heartmula` | obligatorio |
| `--estilo` | uno o más presets o textos libres | `lofi-chill` |
| `--duracion` | segundos que se generan **antes** del recorte (ACE hasta 600, HeartMuLa hasta 240) | 60 |
| `--tono` | tonalidad: `"C Major"`, `"A Minor"`, `"F# Minor"`… | la del preset (obligatoria con texto libre) |
| `--bpm` | tempo, de 30 a 300 | el del preset (obligatorio con texto libre) |
| `--compas` | `2`, `3`, `4` o `6` (2/4, 3/4, 4/4, 6/8) | el del preset, o `4` |
| `--sin-lm` | solo ACE-Step | apagado |
| `--carpeta` | carpeta de salida | `out/music/` |
| `--variantes` | pistas por estilo; con más de 1 los archivos son `<modelo>-<estilo>-v1.wav`, `-v2.wav`… (la melodía cambia en cada una) | 1 |
| `--evaluar` | solo ACE-Step: al final mide con demucs cuánta voz hay en cada pista (ver "Evaluar que no haya voz") | apagado |
| `--reintentos` | con `--evaluar`: rondas que regeneran solo las pistas con voz | 0 |

Si usas texto libre sin `--tono` y `--bpm`, el script se detiene antes de cargar el modelo y muestra el mensaje: `"bossa nova" no es un preset: define --tono y --bpm`. `--tono`, `--bpm` y `--compas` se aplican a **todos** los estilos de esa corrida.

### Estilos predefinidos

| Preset | Descripción | Tonalidad | BPM | Compás |
|:--|:--|:--|:--|:--|
| `lofi-chill` | Rhodes, vinilo, boom bap suave | C Major | 80 | 4/4 |
| `lofi-jazz` | Acordes de jazz, trompeta con sordina, escobillas | D Minor | 85 | 4/4 |
| `lofi-lluvia` | Piano melancólico, ambiente de lluvia | E Minor | 72 | 4/4 |
| `lofi-estudio` | Guitarra suave, groove relajado, minimal | G Major | 78 | 4/4 |
| `lofi-nocturno` | Pads de sintetizador, sub bajo, ciudad de noche | A Minor | 70 | 4/4 |
| `corporate` | Fondo tech optimista, piano eléctrico, plucks | C Major | 110 | 4/4 |
| `future-bass` | Supersaw suaves, sidechain leve, brillante | G Major | 100 | 4/4 |
| `deep-house` | Groove cálido, bajo redondo, elegante | A Minor | 120 | 4/4 |
| `ambient` | Pads que evolucionan, sin batería | D Major | 70 | 4/4 |

Las tonalidades son las que la guía oficial de ACE-Step considera estables: C, G, D, Am, Em y sus vecinas. Las tonalidades poco comunes "pueden ignorarse o desplazarse".

### Catálogo ampliado: 117 presets más

Definidos en [estilos.py](estilos.py); la tabla completa con descripción, tono y BPM está en [ESTILOS.md](ESTILOS.md). Pensados como fondo para tutoriales, publicidad, demos y videos. Cada uno se generó a 30 s con ACE-Step y pasó `--evaluar` (ver más abajo). Se usan igual que los otros: `--estilo <nombre>`.

| Grupo | Presets |
|:--|:--|
| Tutoriales y explicativos | `tutorial-calmo` `tutorial-tech` `tutorial-guitarra` `explainer-animado` `explainer-minimal` `curso-online` `paso-a-paso` `codigo` `documental-suave` |
| Corporativo y publicidad | `corporate-inspirador` `corporate-minimal` `corporate-energico` `corporate-startup` `corporate-confianza` `corporate-innovacion` `corporate-motivacional` `anuncio-alegre` `anuncio-premium` `anuncio-moda` `anuncio-deportivo` `anuncio-comida` `anuncio-lanzamiento` `anuncio-fintech` `anuncio-inmobiliario` `anuncio-salud` `anuncio-viajes` `anuncio-auto` |
| Demos y tecnología | `demo-producto` `demo-saas` `demo-app-movil` `demo-futurista` `demo-ia` `demo-gadget` `demo-ecommerce` `demo-dashboard` `demo-videojuego` |
| Lofi | `lofi-cafe` `lofi-guitarra` `lofi-atardecer` `lofi-nostalgico` `lofi-bossa` `chillhop-foco` `lofi-piano` `vaporwave` |
| Ambient, foco y bienestar | `ambient-espacial` `ambient-piano` `ambient-cinematico` `ambient-bosque` `ambient-oceano` `meditacion` `yoga` `spa` `dormir` `foco-profundo` `new-age` `ambient-oscuro` |
| Cinematográfico | `cinematico-emotivo` `cinematico-esperanza` `trailer-tension` `cinematico-minimal` `documental-naturaleza` `heroico` `misterio` `suspenso-tech` `ciencia-ficcion` `fantasia` `orquesta-calida` `piano-emotivo` `cuerdas-minimal` `neoclasico` |
| Acústico y folk | `acustico-alegre` `acustico-calido` `folk-suave` `country-suave` `piano-pop` `ukulele-playa` `guitarra-clasica` `arpa-celestial` `celta` |
| Jazz, latino y del mundo | `jazz-cafe` `jazz-suave` `bossa-nova` `lounge` `swing-alegre` `latin-suave` `cumbia-suave` `reggae-chill` `afrobeat-ligero` `tropical-house` |
| Electrónica y pop | `pop-brillante` `synthwave` `retrowave-suave` `trap-suave` `drum-and-bass-ligero` `techno-minimal` `house-alegre` `tech-house` `edm-energico` `electropop` `downtempo` `chillwave` `future-garage` `chiptune-alegre` `funk-suave` `disco` `boom-bap` `rnb-suave` `rock-motivacional` `indie-pop` `post-rock-suave` |
| Usos concretos | `navidad-suave` `infantil` `juego-casual` `entrenamiento` `noticias` `cocina` `vlog-viaje` |

**Cómo se probaron**: una pista de 30 s por preset, con LM. Pasa si no tiene voz (`--evaluar`, umbral −25 dB), dura al menos 20 s tras recortar el silencio y no es casi muda. Pasaron 117 de 119: ninguna salió corta ni silenciosa (20,6–30 s, mediana 26,8 s) y se descartaron 2 por voz (ver [INVESTIGACION.md](INVESTIGACION.md)). **Nadie las escuchó**: las métricas no dicen si suenan bien ni si el estilo se reconoce. Con una sola muestra por preset, el resultado es indicativo.

Presets limítrofes en voz (entre −25 y −32 dB, pasaron por poco): `demo-producto`, `heroico`, `suspenso-tech`, `ambient-oceano`, `tutorial-tech`, `ciencia-ficcion`, `pop-brillante`, `demo-saas`. Si los vas a usar, genera con `--evaluar --reintentos 2`.

Bajo una narración, los que mejor acompañan son los de tutoriales y explicativos, `corporate-minimal`, `deep-house` y `ambient`.

Para agregar un preset, suma una entrada a `NUEVOS` en [estilos.py](estilos.py): `nombre: (caption en inglés, tono, bpm[, compás])`. El script agrega `no vocals` al caption y deriva los tags de HeartMuLa. Pruébalo con `--evaluar` antes de confiar en él.

## Evaluar que no haya voz (`--evaluar`)

ACE-Step recibe `[Instrumental]`, pero a veces se le cuela una voz. `--evaluar` separa cada pista con **demucs** (`htdemucs`), mide el nivel del stem de voz respecto de la mezcla y marca como `VOZ` las que superan `VOZ_MAX_DB = -25` dB. Con `--reintentos N` regenera solo esas pistas (semilla nueva) hasta N rondas; si alguna sigue con voz, el script termina con error y las nombra.

```bash
python music/musica.py --modelo acestep --duracion 30 --variantes 4 --evaluar --reintentos 2 \
  --carpeta out/music-variantes --estilo lofi-chill corporate ambient
```

```
  ok   acestep-lofi-chill-v1.wav: voz -39.3 dB respecto de la mezcla
  VOZ  acestep-lofi-chill-v2.wav: voz -4.9 dB respecto de la mezcla
```

- **Por qué demucs y no whisper**: whisper alucina frases sobre música instrumental (`"Outro Music"`, `"Let me know what you think about this video…"`) y marcó como "con voz" pistas que no la tenían. Sus métricas (`no_speech_prob`, `avg_logprob`) no separan la alucinación de la letra real.
- **Calibración del umbral**: pistas instrumentales de ACE-Step, entre −35 y −44 dB; una pista cantada a propósito (letra y `vocal_language='en'`), −4,9 dB. Medido sobre pocas pistas: si aparece un falso positivo o negativo, ajusta `VOZ_MAX_DB`.
- demucs vive solo en `.venv-acestep` (instalado con `--no-deps` para no tocar torch), así que `--evaluar` no funciona con `--modelo heartmula`.
- Cada ronda recarga ACE-Step (~30 s) y carga demucs en la GPU tras liberar la VRAM del generador.

## Cómo funciona ACE-Step (y qué hace `--sin-lm`)

ACE-Step 1.5 usa dos modelos en cadena (fuente: `models/ACE-Step-1.5/docs/en/Tutorial.md` e `INFERENCE.md`):

```
caption + metadatos → [LM 5 Hz, 0.6B] → plan semántico → [DiT turbo, 2B] → audio
```

- **El LM es el "planificador"** (un modelo de lenguaje de 0.6B). Hace tres cosas:
  1. **Completa los metadatos que faltan** (BPM, tonalidad, compás y duración) mediante razonamiento *chain-of-thought*. Si se los das, no los inventa: los usa como restricción al decodificar (`user_metadata`).
  2. **Reescribe y amplía el caption.**
  3. **Genera "códigos semánticos" a 5 Hz**, que contienen la melodía, la orquestación y la estructura. Esos códigos guían al DiT.
- **El DiT es el "ejecutor"**: un modelo de difusión que convierte el plan en audio en 8 pasos. Decide el timbre, la mezcla y los detalles.

**`--sin-lm` apaga el planificador.** El DiT genera directamente a partir del caption y los metadatos (tonalidad, BPM y compás). En consecuencia:

- Es **~3× más rápido**: 12 s contra ~36 s en una pista de 20 s, porque se salta la generación de códigos, que es token a token.
- Ahorra **poca VRAM**: ~0,2 GB.
- **No hay plan de melodía ni de estructura**: el DiT improvisa sobre el caption. La guía oficial lo recomienda cuando "ya tienes los metadatos precisos" y quieres velocidad o control total. Recomienda dejar el LM activo para tener mejor estructura y variedad.
- La tonalidad y el BPM se respetan igual, porque ahora los definen los presets o los flags. En la verificación, `ambient --sin-lm` dio D Major a 69,8 BPM, cuando se pidió D Major a 70 BPM.

En resumen: con el LM, la estructura es mejor y cada corrida da una melodía distinta en la misma tonalidad. Sin el LM, la generación es más rápida y más plana. Conviene usar `--sin-lm` para iterar y el LM para la pista final.

## Rendimiento medido

Equipo: RTX 4060 Laptop, 8 GiB, WSL2. Medido el 2026-10-04 en dos rondas independientes y con los pesos ya descargados. Cada tiempo incluye la carga del modelo.

| | **ACE-Step 1.5 turbo** | **HeartMuLa 3B** |
|:--|:--|:--|
| 1 pista de 30 s | **43–51 s** | **283–296 s** |
| 1 pista de 60 s | **47–51 s** | 296–416 s. Pedí 60 s y entregó 12 s una vez y 42 s otra |
| 5 estilos de 30 s en una sola corrida | **103–121 s** (~15 s por cada pista extra) | no probado |
| 1 pista de 20 s con `--sin-lm` | **12 s** (con LM: ~36 s) | — |
| Pico de VRAM del proceso (nvidia-smi menos la base) | **~6,0 GB** (~5,8 GB con `--sin-lm`) | ~7,1 GB, la GPU llena |
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
| texto libre `--tono "E Minor" --bpm 105` | E Minor, 105 | E Minor; 103 |
| `ambient --sin-lm` | D Major, 70 | D Major; 69,8 |

Es normal que el detector de tempo marque el doble del BPM.

## El silencio final se recorta solo

ACE-Step genera exactamente los segundos pedidos, pero suele **terminar la música antes** y rellenar el resto con silencio. Medido por debajo de −50 dB, quedaron 0,8 s de silencio en pistas de 60 s, entre 0 y 5 s en pistas de 30 s y 10–11 s en pistas de 20 s. El script recorta esa cola con ffmpeg (`areverse,silenceremove,areverse`, umbral `SILENCIO_DB = -50`), así que **la pista final puede durar menos que `--duracion`**. Por ejemplo, `lofi-jazz` pedido a 30 s quedó en 22,5 s.

Por eso conviene pedir **30 s o más**, con margen sobre lo que necesitas.

## Cómo usarlo en un video (guía para la IA)

Flujo recomendado:

1. **Mide la narración primero** (`ffprobe` sobre el `.wav` de `out/narration/`). Pide la música con `--duracion` = narración + 10 s (**mínimo 30**) y revisa los segundos que imprime el script: tienen que cubrir la narración.
2. **Genera 3–5 presets en una sola corrida** con `--duracion 30` (o `--sin-lm` para ir más rápido) para que el usuario elija de oído. Después regenera el elegido con la duración final y con el LM activo. La tonalidad y el BPM se mantienen; la melodía cambia en cada corrida.
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

Tips para el prompt (texto libre de `--estilo`):

- Escríbelo **en inglés y con etiquetas separadas por comas**, siguiendo este orden: género, instrumentos, textura o producción, estado de ánimo y uso. Ejemplo: `"chillhop, nylon guitar, soft keys, vinyl crackle, warm, background music"`. Así están escritos los presets.
- **No pongas el tempo ni la tonalidad en el caption**: van en `--tono` y `--bpm`. La guía oficial lo recomienda así y advierte que, si el caption contradice los metadatos (por ejemplo, "slow ballad" con 160 BPM), el modelo se confunde.
- Agrega `background`, `minimal` o `no drums` cuando la pista va bajo una narración. Una melodía muy cargada compite con la voz.
- Elige un BPM coherente con el género: lofi entre 70 y 90, corporate entre 100 y 120, house entre 118 y 126.

Detalles operativos:

- **El nombre de salida se sobrescribe**: `<modelo>-<estilo>.wav` no lleva fecha. Para guardar variantes, usa `--carpeta out/<proyecto>` o renombra el archivo antes de regenerarlo.
- **Primera corrida**: descarga ~11 GB (ACE-Step) o ~21 GB (HeartMuLa). Si se corta, vuelve a correrla.
- **Logs**: las corridas largas se lanzan en segundo plano y su salida se guarda en `logs/` de la raíz (por ejemplo, `logs/music-<fecha>.log`). HeartMuLa tarda ~5 min por pista.
- **Un modelo a la vez en la GPU**: no generes música mientras corre `narration/tts.py`, porque los dos juntos no caben en 8 GB y el desborde a la RAM compartida hace todo ~4× más lento. Antes de lanzar, revisa la VRAM libre con `nvidia-smi --query-gpu=memory.free --format=csv`: ACE-Step necesita ~6,5 GB. Otros procesos, como el daemon `laya` de Synapse, pueden estar ocupando varios GB.
- El LM `acestep-5Hz-lm-1.7B` también está descargado en `checkpoints/`, pero no se usa: es el perfil de 8–16 GB y necesita vLLM.

## Instalación (desde cero)

Requisitos: `uv`, `git`, `ffmpeg` y una GPU NVIDIA. Los modelos y los venvs quedan dentro de `music/`; `models/` y `.venv-*` están gitignoreados.

```bash
cd music
git clone --depth 1 https://github.com/ACE-Step/ACE-Step-1.5.git models/ACE-Step-1.5
git clone --depth 1 https://github.com/HeartMuLa/heartlib.git models/heartlib

# ACE-Step (Python 3.12, torch 2.10 cu128)
(cd models/ACE-Step-1.5 && UV_PROJECT_ENVIRONMENT=../../.venv-acestep uv sync)

# HeartMuLa (Python 3.10)
uv venv -p 3.10 .venv-heartmula && VIRTUAL_ENV=.venv-heartmula uv pip install -e models/heartlib
```

Los pesos se descargan solos en la primera corrida:
- ACE-Step → `models/ACE-Step-1.5/checkpoints/` (DiT turbo, VAE, Qwen3-Embedding, LMs).
- HeartMuLa → `models/heartmula-ckpt/` (HeartMuLaGen, HeartMuLa-oss-3B-happy-new-year, HeartCodec-oss-20260123).

Si se corta la descarga, vuelve a correr el script: reanuda donde quedó.

Para `--evaluar`, demucs en el venv de ACE-Step (sin dependencias, para no cambiar torch):

```bash
VIRTUAL_ENV=.venv-acestep uv pip install --no-deps demucs
VIRTUAL_ENV=.venv-acestep uv pip install julius einops lameenc openunmix dora-search
```

Los venvs no se pueden mover de carpeta, porque guardan rutas absolutas. Si mueves `music/`, borra los `.venv-*` y vuelve a crearlos con los comandos de arriba (con la caché de uv tarda poco).

## Estructura

```
music/
├── README.md          # este archivo
├── INVESTIGACION.md   # modelos evaluados, descartes y fuentes
├── musica.py          # script
├── models/            # repos clonados y pesos (gitignoreado)
├── .venv-acestep/     # gitignoreado
└── .venv-heartmula/   # gitignoreado
```

Las salidas van a `out/music/` y los logs a `logs/`, ambos en la raíz del repo y gitignoreados.

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
- **ACE-Step con OOM**: cierra las apps que estén usando la GPU o usa `--sin-lm`.

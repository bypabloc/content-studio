# Spec: Motores de VoiceStudio, Emoción y Masterización en `narration/tts.py`

> Spec del 2026-11-15. Todo lo necesario para implementar en `narration/tts.py` los cuatro motores investigados (OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3), una gramática de guion con estilo y emoción por párrafo y gestos traducidos por motor, semilla reproducible, metadatos por toma, masterización de precisión y `--evaluar` adaptado. **Implementado** en `feature/motores-voicestudio`: este documento sigue siendo el contrato, y las desviaciones están en la §15. Base: [docs/research/voicestudio-narracion/](../research/voicestudio-narracion/README.md).

---

## 0. Decisiones del Usuario (2026-11-15)

| # | Pregunta | Decisión | Consecuencia en esta spec |
| :--- | :--- | :--- | :--- |
| 1 | ¿Qué motores? | **Los cuatro**, comerciales y no comerciales: es software personal | §3: OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3 como `--modelo` |
| 2 | ¿Monetización? | **Los videos son personales** | La licencia se informa en la salida y en los metadatos; no bloquea |
| 3 | Referencias | **Grabar el kit**; indicar qué grabar y qué decir | [narration/docs/guiones/](../../narration/docs/guiones/README.md) actualizado: 12 clips + 6 de emoción (hecho en este PR) |
| 4 | Masterización | **La más precisa** | §7: normalización de loudness lineal de dos pasadas, sin compresión |
| 5 | Emoción por párrafo y traducción de marcas | **Sí** | §5 y §6 |
| 6 | Corregir las guías que contradicen lo medido | **Sí** | Hecho en este PR: `guiones/`, `formato-guion.md`, `.gitignore` |
| 7 | Disco | **Eliminar lo innecesario** | Hecho: imagen Docker (17.8 GB), pesos sin uso de CosyVoice (4.3 GB) y el clon de VoiceStudio. Se conservan los motores y sus pesos para la implementación (§2) |

---

## 1. Objetivos y No Objetivos

**Objetivos**

1. `python narration/tts.py --modelo {omnivoice,voxcpm2,indextts,cosyvoice3} …` genera narración con la misma interfaz que hoy (`--estilo`, `--texto`/`--archivo`, JSON, `--salida`, pausas, `--evaluar`, `--reintentos`).
2. Un guion puede cambiar de **estilo** (referencia) y de **emoción** por párrafo, y pedir **gestos** (risa, suspiro, respiro, énfasis) con una sintaxis única en español que `tts.py` traduce o quita según el motor.
3. Toda toma es **reproducible**: semilla registrada y metadatos completos al lado del `.wav`.
4. Salida con **loudness exacta** (−16 LUFS, pico real ≤ −1.5 dBTP) sin alterar la dinámica.
5. `--evaluar` sigue funcionando con los seis motores y cambia de semilla en cada reintento.

**No objetivos (de esta implementación)**

* Usar la app VoiceStudio o su API (se replicó, no se integra: [14](../research/voicestudio-narracion/14-replicacion-de-voicestudio.md)).
* Fine-tuning de modelos ([herramientas/15](../research/voicestudio-narracion/herramientas/15-entrenamiento-y-fine-tuning.md)).
* Las ideas de §12 (subtítulos, marca de agua, comparador de motores, preset `broadcast`): quedan como fases posteriores.

---

## 2. Disposición de Archivos y Entornos

### 2.1 Estado Actual (Tras la Investigación)

| Motor | Dónde está hoy | Pesos |
| :--- | :--- | :--- |
| OmniVoice | `narration/.venv-omnivoice` (Python 3.12, `omnivoice` 0.2.1, `torch==2.14.1`) | `~/.cache/huggingface` (`k2-fsa/OmniVoice`) |
| VoxCPM2 | `narration/.venv-voxcpm` (Python 3.12, `voxcpm` 2.0.3, `torch==2.14.1`) | `~/.cache/huggingface` (`openbmb/VoxCPM2`) |
| IndexTTS 2.5 | `tmp/research-vs/repos/index-tts` con su `.venv` (Python 3.11, torch 2.8 cu128) | `…/index-tts/checkpoints` (11 GB, incluye `hf_cache/`) |
| CosyVoice 3 | `tmp/research-vs/repos/CosyVoice` con su `.venv` (Python 3.10, `torch==2.14.1`, `setuptools<80`, sin `wetext`) | `…/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B` (5.4 GB) |

### 2.2 Destino

```
narration/
├── tts.py
├── motores/                      # NUEVO, gitignoreado: repos de motores que no son paquetes pip
│   ├── index-tts/                # mover desde tmp/research-vs/repos/ (con .venv y checkpoints)
│   └── CosyVoice/                # ídem
├── .venv-qwen/  .venv-chatterbox/  .venv-omnivoice/  .venv-voxcpm/
└── voz/                          # referencias: <estilo>.wav (gitignoreado) + <estilo>.txt
    └── emociones/                # clips opcionales para IndexTTS (gitignoreado)
```

* Agregar `narration/motores/` al `.gitignore`.
* Mover con `mv`, no reinstalar: los venvs de los repos usan rutas absolutas en sus scripts de `bin/`. **Después de mover, recrear el `.venv` de cada repo** (`uv sync` en IndexTTS; `uv venv` + `uv pip install` en CosyVoice, §2.3), porque un venv movido deja de funcionar. Los pesos sí se mueven sin problema.
* IndexTTS crea `checkpoints/hf_cache` **relativo al directorio actual** en la primera carga (en la investigación apareció un `checkpoints/` suelto en la raíz del repo): `cargar_indextts` debe hacer `os.chdir` al repo, o fijar `HF_HUB_CACHE` en `motores/index-tts/checkpoints/hf_cache` antes de importar.

### 2.3 Instalación (Va a `narration/README.md` §2)

```bash
# OmniVoice y VoxCPM2 (pip). torch 2.15 da segfault en esta WSL: fijar 2.14.1
uv venv -p 3.12 narration/.venv-omnivoice
VIRTUAL_ENV=narration/.venv-omnivoice uv pip install omnivoice soundfile "torch==2.14.1" "torchaudio==2.11.1"
uv venv -p 3.12 narration/.venv-voxcpm
VIRTUAL_ENV=narration/.venv-voxcpm uv pip install voxcpm soundfile "torch==2.14.1" "torchaudio==2.11.1"

# IndexTTS 2.5 (repo)
git clone --depth 1 https://github.com/index-tts/index-tts narration/motores/index-tts
(cd narration/motores/index-tts && uv sync --python 3.11 --extra webui \
  && uv tool run --from 'huggingface_hub[cli]' hf download IndexTeam/IndexTTS-2.5 --local-dir=checkpoints)

# CosyVoice 3 (repo): quitar deps de TRT/deepspeed/whisper fijado/gradio; setuptools<80; sin wetext
git clone --depth 1 --recursive https://github.com/FunAudioLLM/CosyVoice narration/motores/CosyVoice
cd narration/motores/CosyVoice && uv venv -p 3.10 .venv
grep -v -i -E '^(torch|torchaudio|deepspeed|tensorrt|onnxruntime-gpu|--extra-index-url|openai-whisper|gradio)' requirements.txt > req-social-videos.txt
VIRTUAL_ENV=.venv uv pip install "torch==2.14.1" "torchaudio==2.11.1" -r req-social-videos.txt onnxruntime openai-whisper huggingface_hub "setuptools<80"
VIRTUAL_ENV=.venv uv pip uninstall wetext
.venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir='pretrained_models/Fun-CosyVoice3-0.5B', ignore_patterns=['llm.rl.pt','*.fp32.onnx','*.batch.onnx'])"
```

Cada venv necesita además `numpy` y `soundfile` (los importa `tts.py`); verificar con `<venv>/bin/python -c "import numpy, soundfile"` y agregarlos al comando si faltan.

### 2.4 Compatibilidad de `tts.py` con Python 3.10–3.12

`usar_venv` relanza **el mismo `tts.py`** con el Python del venv del motor. El venv de CosyVoice es **3.10**: `tts.py` no puede usar sintaxis posterior a 3.10. Hoy usa `str | None` y `:=`, ambos válidos en 3.10; la implementación no debe agregar nada de 3.11+ (por ejemplo `except*` o `typing.Self`). Agregar un doctest o una prueba de humo que importe `tts.py` con cada venv (§10).

---

## 3. Registro de Motores

Reemplazar `MODELOS` y el `if modelo == 'chatterbox'` de `regenerar` por un registro único. Cada entrada describe cómo cargar, generar y qué entiende el motor.

```python
# Esquema (nombres finales a criterio de la implementación; mantener el estilo funcional del archivo)
MOTORES = {
    'qwen-1.7b':  dict(venv='.venv-qwen', repo='Qwen/Qwen3-TTS-12Hz-1.7B-Base', pesos=3.95, lote=True,
                       licencia='Apache-2.0', comercial=True,  usa_txt=True,  ref_max_s=60,
                       gestos=set(), emocion=None, sr=24000),
    'qwen-0.6b':  dict(…, pesos=2.06),
    'chatterbox': dict(venv='.venv-chatterbox', repo='v3', licencia='MIT', comercial=True, usa_txt=False,
                       ref_max_s=10, gestos=set(), emocion='parametros', sr=24000),
    'omnivoice':  dict(venv='.venv-omnivoice', repo='k2-fsa/OmniVoice', licencia='CC-BY-NC + Higgs Audio 2',
                       comercial=False, usa_txt=True, ref_max_s=10, gestos={'risa', 'suspiro'},
                       emocion=None, sr=24000, vram_gib=2.22),
    'voxcpm2':    dict(venv='.venv-voxcpm', repo='openbmb/VoxCPM2', licencia='Apache-2.0', comercial=True,
                       usa_txt=True, ref_max_s=30, gestos=set(), emocion='instruccion', sr=48000, vram_gib=5.75),
    'indextts':   dict(venv='motores/index-tts/.venv', repo='motores/index-tts/checkpoints',
                       licencia='bilibili Model Use License', comercial=False, usa_txt=False, ref_max_s=15,
                       gestos=set(), emocion='vector', sr=22050, vram_gib=5.69),
    'cosyvoice3': dict(venv='motores/CosyVoice/.venv', repo='motores/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B',
                       licencia='Apache-2.0 (card: "academic purposes")', comercial=True, usa_txt=True,
                       ref_max_s=30, gestos={'risa', 'suspiro', 'respiro', 'enfasis'},
                       emocion='instruccion', sr=24000, vram_gib=3.50),
}
```

* `usar_venv` acepta rutas con subcarpetas (`motores/index-tts/.venv`).
* Si `comercial` es `False`, imprimir **una línea** antes de generar: `Aviso: <motor> tiene licencia no comercial (<licencia>). Solo uso personal.` y guardarlo en los metadatos. No bloquea (decisión 2).
* Si la referencia dura más que `ref_max_s`, avisar (el motor la recorta; Chatterbox usa 6 s de estilo).
* `lote` solo es `True` en Qwen; el resto genera de a un bloque (`lote_auto` solo aplica a Qwen).

### 3.1 Carga y Generación por Motor

Todas las funciones de carga con `@lru_cache` y una función `liberar()` que limpie las cachés y llame `torch.cuda.empty_cache()` (hoy `main` llama a mano `cargar_qwen.cache_clear()` y `cargar_chatterbox.cache_clear()`: generalizar).

| Motor | Carga | Generación de un bloque | Notas medidas |
| :--- | :--- | :--- | :--- |
| `omnivoice` | `OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cuda', dtype=torch.float16)` | `prompt = create_voice_clone_prompt(ref_audio, ref_text)` **cacheado por referencia**; `generate(text, language=idioma, voice_clone_prompt=prompt, num_step=32, guidance_scale=2.0)[0]` | Siempre con `ref_text` (sin él carga Whisper y puede quedarse sin VRAM). 24 kHz |
| `voxcpm2` | `VoxCPM.from_pretrained('openbmb/VoxCPM2', load_denoiser=False, optimize=False)` | **Sin emoción (Hi-Fi):** `generate(text, reference_wav_path=ref, prompt_wav_path=ref, prompt_text=ref_txt, cfg_value=2.0, inference_timesteps=10, retry_badcase_max_times=1, max_len=min(4096, max(256, len(text)*6)))`. **Con emoción (controlable):** `generate(f'({instr}){text}', reference_wav_path=ref, …)` sin `prompt_*` | En Hi-Fi la instrucción **se lee**: nunca combinarlas. 48 kHz. Primera carga ~100 s |
| `indextts` | `IndexTTS2(cfg_path=…/config.yaml, model_dir=…/checkpoints, use_bf16=True, use_cuda_kernel=False, use_deepspeed=False, use_qwen_emo=False)` | `infer(spk_audio_prompt=ref, text, lang=idioma, output_path=tmp, emo_vector=v, emo_alpha=a, emo_audio_prompt=clip, verbose=False)`; leer `tmp` | `use_qwen_emo=False` siempre (con `True` desborda 8 GB y va 5× más lento). Vector normalizado (§6.2). 22.05 kHz. Escribe a disco: usar un temporal en `/dev/shm` o `tmp/` |
| `cosyvoice3` | `sys.path` += repo y `third_party/Matcha-TTS`; **reemplazar `torchaudio.load` por una lectura con soundfile** (torchaudio 2.11 exige torchcodec); `AutoModel(model_dir)` | **Sin emoción:** `inference_zero_shot(text, 'You are a helpful assistant.<\|endofprompt\|>' + ref_txt, ref, stream=False, text_frontend=False)`. **Con emoción:** `inference_instruct2(text, f'You are a helpful assistant. {instr}<\|endofprompt\|>', ref, stream=False, text_frontend=False)`. Concatenar los `tts_speech` | `instruct2` ignora la entrega de la referencia. 24 kHz |
| `qwen-*`, `chatterbox` | Igual que hoy | Igual que hoy, más semilla (§4) | — |

La semilla se fija antes de **cada** bloque (§4). VoxCPM2 además acepta `seed=` en `generate`.

---

## 4. Semilla y Reproducibilidad

* Nuevo flag `--semilla N`. Por defecto, aleatoria (`random.randrange(2**31)`) y **siempre impresa y guardada** en los metadatos.
* Antes de generar cada bloque: `random.seed(s); numpy.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)` con `s = semilla_base + ronda`. Todos los bloques de una ronda usan la **misma** semilla, como hace VoiceStudio (#3730: si avanza por bloque, la voz cambia a mitad de la toma).
* **Reintentos:** la ronda `r` de `--reintentos` usa `semilla_base + r`. Si se usara la misma semilla, el bloque fallido saldría idéntico.
* Reproducibilidad esperada: misma máquina, motor, referencia, texto y semilla → misma salida (salvo no determinismo de kernels de GPU; la réplica de VoiceStudio mostró que `torch.compile` cambia el resultado: **no compilar** ningún motor).
* Doctest de la función que calcula la semilla de cada bloque y ronda.

---

## 5. Gramática del Guion

Todo en español, independiente del motor. `tts.py` la interpreta; **ninguna marca llega al modelo sin traducir**.

| Marca | Alcance | Significado | Ejemplo |
| :--- | :--- | :--- | :--- |
| Línea en blanco | — | Pausa de párrafo (0.6 s), como hoy | |
| `[pausa N]` | — | Silencio de N s, como hoy | `[pausa 1,5]` |
| `[estilo: nombre]` | Desde ese punto hasta el próximo `[estilo:]` | Cambia la referencia (`voz/<nombre>.wav` + `.txt`) y los parámetros de `ESTILOS` | `[estilo: dramatica]` |
| `[emocion: nombre]` o `[emocion: nombre 0.4]` | Desde ese punto hasta el próximo `[emocion:]`; `[emocion:]` vacío vuelve a ninguna | Emoción del vocabulario §6.1, con intensidad opcional entre 0 y 1 (por defecto 0.6) | `[emocion: triste]` |
| `[risa]`, `[suspiro]`, `[respiro]` | En el lugar donde se escriben | Gesto no verbal (§6.3) | `me dijo que sí [risa] no lo podía creer` |
| `[enfasis]…[/enfasis]` | La palabra encerrada | Énfasis (§6.3) | `es [enfasis]gratis[/enfasis] para siempre` |

Reglas:

1. `[estilo:]` y `[emocion:]` **cortan el bloque**: un cambio de estilo o emoción nunca cae a mitad de un bloque generado. Si aparecen a mitad de una oración, `tts.py` avisa (VoiceStudio: un cambio de emoción a mitad de oración rompe la entonación).
2. Un `[estilo:]` sin `voz/<nombre>.wav` es un error antes de generar (como hoy `No existe la referencia`).
3. En JSON, las marcas van dentro de los strings de `texto` (sin cambiar el formato). Opcional: un párrafo puede ser un objeto `{"texto": "...", "estilo": "...", "emocion": "triste 0.4"}`, equivalente a anteponer las marcas.
4. `etiquetas()` (el aviso actual) deja de marcar las palabras de esta gramática y sigue avisando de todo lo demás (`[breath]`, `<break>`, `**`, `(pausa)`).
5. Para `--evaluar`, el texto esperado es el texto **sin** marcas (los gestos no son palabras).

### 5.1 Cambios en `segmentos`

Hoy devuelve `[(texto, pausa)]`. Pasa a devolver bloques con estado:

```python
[{'texto': 'Nadie sabía…', 'pausa': 0.6, 'estilo': 'dramatica', 'emocion': ('miedo', 0.6)}, …]
```

`MARCA_PAUSA` se generaliza a un tokenizador de marcas (pausa, línea en blanco, estilo, emoción); gestos y énfasis quedan dentro del texto del bloque y se traducen en §6.3 justo antes de llamar al motor. Mantener y ampliar los doctests actuales de `segmentos`.

### 5.2 Agrupación en Qwen

El lote de Qwen usa un único `voice_clone_prompt`. Con estilos por párrafo, agrupar los bloques **por referencia** y cachear un prompt por referencia (`dict` por ruta).

---

## 6. Traducción por Motor

### 6.1 Vocabulario de Emociones

| Emoción | IndexTTS (vector¹) | VoxCPM2 (instrucción) | CosyVoice 3 (`instruct2`) | Chatterbox (`exaggeration`, `cfg_weight`) | Qwen y OmniVoice |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `alegre` | happy | `cheerful and energetic` | `Please speak in a cheerful and energetic tone.` | 0.7, 0.3 | Usa la referencia `energica` si existe; si no, aviso |
| `triste` | sad | `sad and slow` | `Please speak in a sad and slow tone.` | 0.4, 0.5 | `triste` |
| `enojado` | angry | `angry and firm` | `Please speak in an angry tone.` | 0.8, 0.3 | Aviso (sin referencia) |
| `miedo` | afraid | `tense and fearful` | `Please speak in a fearful tone.` | 0.6, 0.3 | `dramatica` |
| `sorpresa` | surprised | `surprised and amazed` | `Please speak in a surprised tone.` | 0.7, 0.3 | `amistosa` |
| `calma` | calm | `calm and confident` | `Please speak in a calm, warm tone.` | 0.3, 0.5 | `suave` |
| `urgente` | afraid 0.5 + surprised 0.3 | `urgent, speaking fast` | `Please speak in an urgent tone, speaking fast.` | 0.7, 0.3 | `energica` |
| `susurro` | — (aviso: usar `[estilo: intima]`) | `whispering` | — (aviso: no lo sigue) | — | `intima` |

¹ Orden `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`.

* Las instrucciones van **en inglés** (medido: en español cambian menos en VoxCPM2 y se leyeron 1 de 10 veces en CosyVoice). Cortas, sin palabras que amortigüen ("quiet", "flat").
* Intensidad: en IndexTTS es `emo_alpha` (por defecto 0.6, máximo 1.0); en Chatterbox escala la diferencia respecto de 0.5; en VoxCPM2 y CosyVoice se ignora (aviso si se pasó).
* Con IndexTTS, si existe `voz/emociones/<emocion>.wav` (§ guion 11), usar `emo_audio_prompt` en lugar del vector (flag `--emocion-clip` o automático; decidir en implementación, por defecto automático).
* "Qwen y OmniVoice": la emoción **cambia la referencia** del bloque a la indicada si `voz/<estilo>.wav` existe; si no, aviso y se genera sin emoción.

### 6.2 Normalización del Vector (IndexTTS)

Replicar la de su WebUI (`infer()` no la aplica): multiplicar por `[0.9375, 0.875, 1.0, 1.0, 0.9375, 0.9375, 0.6875, 0.5625]` y, si la suma supera 0.8, escalar a 0.8. Doctest con los valores de §6.1.

### 6.3 Gestos, Énfasis y Texto

| Marca del guion | omnivoice | voxcpm2 | indextts | cosyvoice3 | qwen / chatterbox |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[risa]` | `[laughter]` | quitar | quitar | `[laughter]` | quitar |
| `[suspiro]` | `[sigh]` | quitar | quitar | `[sigh]` | quitar |
| `[respiro]` | quitar | quitar | quitar | `[breath]` | quitar |
| `[enfasis]x[/enfasis]` | `x` | `x` | `x` | `<strong>x</strong>` | `x` |
| `…` a mitad de oración | **`,`** (omite lo que sigue) | dejar | dejar | dejar | dejar |
| `—` | dejar | dejar | **`,`** (lo lee "menos") | dejar | dejar |
| `(` `)` `*` | dejar | **quitar** (`(` activa el modo instrucción; issue #216) | dejar | dejar | dejar |
| Dígitos | dejar | dejar | **aviso** (lee mal: "mil cimientos") | dejar | aviso (regla 13) |

* Cada "quitar" o reemplazo genera una línea de aviso (`Aviso: <motor> no soporta [respiro]; se quitó en el párrafo 3`) y queda en los metadatos.
* La tabla sale de lo **medido** en [13](../research/voicestudio-narracion/13-pruebas-en-gpu.md) §4. Implementarla como datos (un `dict` por motor), no como `if` dispersos, con doctests por motor.
* Nunca enviar `[pause]`, `<strong>` ni `[breath]` a OmniVoice: rompen la salida o se leen.

---

## 7. Masterización de Precisión

Decisión 4: **la más precisa**. Se elige normalización de loudness **lineal de dos pasadas** y no la cadena `broadcast` de VoiceStudio:

| Opción | Qué hace | Por qué no es la elegida / por qué sí |
| :--- | :--- | :--- |
| Sin procesar | Lo que da el motor | Loudness distinta entre motores y estilos (medido: −13.7 a −21.8 LUFS entre frases de OmniVoice en la réplica) |
| `broadcast` (VoiceStudio) | HPF, compresor, nivelador, EQ, limitador, pico −2 dBFS | Cambia la dinámica y el timbre; normaliza por **pico**, no por loudness, así que dos tomas quedan a volúmenes percibidos distintos (−15.9 a −20.7 LUFS en la réplica) |
| **`voz` (elegida)** | HPF 70 Hz + ganancia lineal medida para −16 LUFS + techo de pico real −1.5 dBTP | **No altera la dinámica ni el timbre**; el volumen percibido queda exacto (±0.5 LU) y comparable entre motores, estilos y videos |

### 7.1 Algoritmo (`--master voz`, por defecto)

1. Después de unir bloques y aplicar `atempo` (hoy en `escribir`).
2. Filtro pasa-altos de 70 Hz (`highpass=f=70`): quita retumbo sin tocar la voz.
3. **Pasada 1**: medir con `loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json` → `input_i`, `input_tp`, `input_lra`, `input_thresh`, `target_offset`.
4. **Pasada 2**: aplicar `loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:measured_I=…:measured_TP=…:measured_LRA=…:measured_thresh=…:offset=…`.
5. Si ffmpeg informa `normalization_type: dynamic` (no pudo ser lineal porque el pico real superaría −1.5 dBTP), **avisar** y guardar el dato: el audio queda a menos de −16 LUFS pero sin compresión.
6. **Pasada 3 (verificación)**: medir de nuevo con `ebur128=peak=true`; guardar `lufs_final` y `pico_real_final` en los metadatos. Criterio de aceptación: |LUFS − (−16)| ≤ 0.5 cuando fue lineal; pico real ≤ −1.5.
7. Escribir WAV **24 bits** a la frecuencia nativa del motor (no remuestrear: VoxCPM2 queda en 48 kHz).

**Por qué −16 LUFS:** es el estándar de voz hablada para podcasts y móviles (Apple, Spotify), y deja 2 LU de margen bajo los −14 LUFS a los que normalizan YouTube, TikTok e Instagram, para mezclar después la música de `music/` sin saturar. **Por qué −1.5 dBTP:** evita la distorsión al convertir a AAC/MP3 en las plataformas.

### 7.2 Flags

* `--master voz` (por defecto), `--master no` (salida del motor sin procesar, para comparar y evaluar).
* `--lufs -16` para cambiar el objetivo (por ejemplo −14 si la voz va sola).
* La masterización se aplica al `.wav` final; `--evaluar` sigue transcribiendo los bloques sin masterizar.

---

## 8. Metadatos por Toma

Junto a cada `salida.wav`, un `salida.json`:

```json
{
  "version_tts": "<git rev-parse --short HEAD>",
  "fecha": "2026-11-20T10:00:00-05:00",
  "motor": "voxcpm2", "licencia": "Apache-2.0", "comercial": true,
  "idioma": "es", "semilla": 123456789, "semillas_por_ronda": [123456789, 123456790],
  "master": {"modo": "voz", "lufs_objetivo": -16, "lufs_final": -16.1, "pico_real_final": -2.3, "tipo": "linear"},
  "bloques": [
    {"i": 1, "texto_guion": "…", "texto_enviado": "…", "estilo": "experta", "referencia": "narration/voz/experta.wav",
     "referencia_sha256": "…", "emocion": null, "modo": "hifi", "pausa_despues": 0.6,
     "inicio_s": 0.0, "fin_s": 3.4, "avisos": []}
  ],
  "parametros": {"cfg_value": 2.0, "inference_timesteps": 10, "velocidad": 1.0},
  "tiempo_generacion_s": 21.4, "duracion_s": 12.8, "vram_pico_gib": 5.75,
  "evaluacion": {"rondas": 2, "observaciones": ["…"], "ok": true}
}
```

* `texto_enviado` es lo que realmente recibió el motor tras §6.3: permite auditar cualquier lectura rara.
* El hash de la referencia detecta si se regrabó una voz entre dos tomas.

---

## 9. `--evaluar` y `--reintentos`

* `liberar()` genérico antes de cargar whisper (hoy solo limpia Qwen y Chatterbox).
* Semilla nueva por ronda (§4).
* `--idioma en`: pasar `--language en` a whisper y no aplicar la normalización de números y siglas en español (`normalizar` usa `en_palabras` y `LETRA`, que son de español).
* Normalizar el texto esperado **sin marcas** (§5 regla 5).
* Las observaciones por bloque se agregan a los metadatos (§8).
* Con OmniVoice, `--evaluar` es especialmente importante (omisiones). Sugerir en la salida: `Sugerencia: usa --evaluar con omnivoice` si no se pasó.

---

## 10. Flags Nuevos (Resumen)

| Flag | Valores | Por defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--modelo` | + `omnivoice`, `voxcpm2`, `indextts`, `cosyvoice3` | requerido | §3 |
| `--estilo` | + `neutral`, `energica`, `dramatica`, `triste`, `intima`, `susurro`, `neutral-en` | `experta` (`neutral-en` si `--idioma en`) | Referencia inicial del guion |
| `--idioma` | `es`, `en` | `es` | Idioma del motor y de whisper |
| `--semilla` | entero | aleatoria (registrada) | §4 |
| `--master` | `voz`, `no` | `voz` | §7 |
| `--lufs` | número | −16 | §7.2 |

`ESTILOS` agrega (valores iniciales, ajustables tras grabar):

| Estilo | velocidad | temperature | exaggeration | cfg_weight |
| :--- | :--- | :--- | :--- | :--- |
| `neutral` | 1.0 | 0.7 | 0.5 | 0.5 |
| `energica` | 1.0 | 0.8 | 0.7 | 0.3 |
| `dramatica` | 1.0 | 0.7 | 0.6 | 0.3 |
| `triste` | 1.0 | 0.7 | 0.4 | 0.5 |
| `intima` | 1.0 | 0.7 | 0.4 | 0.5 |
| `susurro` | 1.0 | 0.7 | 0.3 | 0.5 |
| `neutral-en` | 1.0 | 0.7 | 0.5 | 0.5 |

---

## 11. Pruebas y Criterios de Aceptación

### 11.1 Automáticas (doctests, corren con `python3 -m doctest narration/tts.py`)

* `segmentos`: los doctests actuales siguen pasando; nuevos para `[estilo:]`, `[emocion:]`, `[emocion:]` vacío, intensidad, marcas a mitad de oración y combinación con `[pausa N]`.
* Traducción §6.3: un caso por motor y por marca.
* Vector §6.2 y semillas §4.
* `etiquetas()`: no marca la gramática nueva; sigue marcando `[breath]`, `<break>`, `**`.
* Prueba de humo: `<venv>/bin/python -c "import ast; ast.parse(open('narration/tts.py').read())"` con los cuatro venvs nuevos (Python 3.10, 3.11 y 3.12).

### 11.2 Con GPU (manual, documentado en el PR de implementación)

Con la referencia de prueba y luego con el kit grabado:

| # | Prueba | Criterio |
| :--- | :--- | :--- |
| 1 | Cada motor genera `c_tutorial` (13 §3.1) con `--evaluar` | `OK` en los 4 motores |
| 2 | OmniVoice con "despacio… y no había nadie" | Tras §6.3 (`…` → `,`), whisper oye la frase completa en 2 de 2 semillas |
| 3 | IndexTTS con "revisa el texto — y guarda" | No aparece "menos" |
| 4 | VoxCPM2 con `[emocion: alegre]` | La instrucción no se lee; modo controlable en los metadatos |
| 5 | CosyVoice con `[risa]` y `[respiro]` | No se leen; whisper no los transcribe |
| 6 | Guion con `[estilo: dramatica]` a mitad | Dos referencias distintas en los metadatos; el corte cae entre bloques |
| 7 | `--semilla 1` dos veces | Misma duración por bloque y correlación de onda > 0.9 (motores sin `torch.compile`) |
| 8 | `--reintentos 2` | Las semillas por ronda difieren y quedan en los metadatos |
| 9 | `--master voz` | LUFS final −16 ± 0.5 y pico real ≤ −1.5 dBTP en los 6 motores |
| 10 | VRAM | Pico ≤ 6.5 GiB en todos los motores con bloques de ~300 letras |
| 11 | `--idioma en` con `neutral-en` | `--evaluar` en inglés sin falsos errores de números |

### 11.3 Validación con la Voz Real (Tras Grabar el Kit)

Repetir el banco de la investigación (`tmp/research-vs/banco.py` y `analizar.py`, o su versión incorporada de §12) con `voz/neutral.wav` y `voz/experta.wav` en los seis motores, escuchar las salidas y fijar en el README el motor por defecto para cada tipo de video ([07](../research/voicestudio-narracion/07-comparativa-y-licencias.md) §5).

---

## 12. Ideas para Fases Posteriores

| Idea | Valor | Base |
| :--- | :--- | :--- |
| **Comparador de motores** (`narration/comparar.py`): misma frase en todos los motores con una referencia y tabla de WER, palabras/s, F0 y VRAM | Elegir motor con la voz real; regresiones | Banco de la investigación ([13](../research/voicestudio-narracion/13-pruebas-en-gpu.md)) |
| **Subtítulos** SRT y ASS por palabra a partir de whisper con `word_timestamps`, re-segmentados para formato vertical | Reels con subtítulos sin otra herramienta | [herramientas/08](../research/voicestudio-narracion/herramientas/08-transcripcion.md) |
| `--master broadcast`: la cadena de VoiceStudio replicada | Sonido "de radio" cuando se busque | [14](../research/voicestudio-narracion/14-replicacion-de-voicestudio.md) §2 |
| Marca de agua AudioSeal (`--marca`) | Publicación responsable | [herramientas/13](../research/voicestudio-narracion/herramientas/13-marca-de-agua.md) |
| Multivoz (`[voz: nombre]`) para diálogos | Storytelling con personajes | [herramientas/03](../research/voicestudio-narracion/herramientas/03-audiolibros-e-historias.md) |
| Gramática `[lento]…[/lento]`, `[rapido]…[/rapido]` con `atempo` por tramo | Ritmo puntual | VoiceStudio longform |
| Diccionario de pronunciación (`narration/pronunciacion.json`: "Klinikae" → "Clinikái") aplicado antes de §6.3 | Respelling automático y consistente | Regla 16; VoiceStudio `[[…]]` |
| `num2words` en español para convertir dígitos antes de IndexTTS | Menos reescritura manual | Medido: IndexTTS lee mal los dígitos |
| Room tone en las pausas en vez de silencio digital | Pausas menos "cortadas" | VoiceStudio `pause_fill` |
| Lotes en OmniVoice (acepta listas en `generate`) | Más velocidad | `omnivoice.generate` |

---

## 13. Plan de Implementación

| Fase | Contenido | Entregable |
| :--- | :--- | :--- |
| F0 | Mover repos a `narration/motores/`, recrear sus venvs, `.gitignore`, comandos de §2.3 en el README | Instalación reproducible |
| F1 | Registro de motores (§3), carga y generación de los 4 motores con referencia de estilo, semilla (§4), metadatos (§8) | `--modelo` nuevos funcionando |
| F2 | Gramática (§5) y traducción por motor (§6) con doctests | Estilo y emoción por párrafo, gestos |
| F3 | Masterización `voz` (§7) | Loudness exacta |
| F4 | `--evaluar` y `--reintentos` adaptados (§9), `--idioma en` | Evaluación en los 6 motores |
| F5 | Documentación: `narration/README.md` (instalación, flags, rendimiento medido, estilos nuevos) y `formato-guion.md` (gramática nueva) | Docs al día |
| F6 | Pruebas de §11.2 y validación con la voz real (§11.3) | Motor por defecto por tipo de video |

Rama sugerida: `feature/motores-voicestudio` desde `dev`, un commit por fase.

---

## 14. Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| Mover los repos rompe sus venvs | Recrearlos tras mover (§2.2); los pesos no se tocan |
| VoxCPM2 y CosyVoice cambian de API en una versión nueva | Fijar versiones: `voxcpm==2.0.3`; commit del clon de CosyVoice e IndexTTS registrado en el README |
| `tts.py` relanzado con Python 3.10 (CosyVoice) | §2.4 y prueba de humo §11.1 |
| Instrucción en inglés poco fiel en algunas voces | Generar 2–3 tomas (`--semilla` distinta) y elegir; `--evaluar` |
| La referencia propia cambia el ranking de motores | §11.3 antes de fijar valores por defecto |
| Licencias no comerciales usadas por error en un video monetizado | Aviso en cada ejecución y campo `comercial` en los metadatos |

---

## 15. Desviaciones de la implementación

Lo que quedó distinto de este contrato, y por qué.

| # | Spec | Qué quedó | Motivo |
| :--- | :--- | :--- | :--- |
| 1 | §3.1: VoxCPM2 acepta `seed=` en `generate` | No lo acepta (voxcpm 2.0.3). La semilla se fija con `random`, `numpy` y `torch` antes de cada bloque | El parámetro solo existe en el acelerador de entrenamiento |
| 2 | §7.1: −16 LUFS y −1.5 dBTP sin compresión | Con −16 LUFS, la normalización lineal solo cabe si pico real − loudness ≤ 14.5 dB. Si no, queda `dynamic`, que limita el pico: se avisa y se registra en `master.tipo`. Las salidas de OmniVoice pasan de ese límite; para que sea lineal hace falta un objetivo más bajo (≈ −19 LUFS) | El limitador reduce el rango de loudness (medido: LRA 3.5 → 2.7 LU) |
| 3 | §7.1: WAV a la frecuencia nativa | Se añade `aresample` tras `loudnorm` | `loudnorm` escribe a 192 kHz |
| 4 | §5.1: `segmentos` devuelve bloques con estado | Devuelve diccionarios; los doctests de pausas conservan sus expectativas | Forma pedida por el spec |
| 5 | §5: `[estilo:]` sin `voz/<nombre>.wav` es un error | Igual con `--ref` carpeta. Con `--ref` de un solo archivo el estilo no cambia la referencia y no hay error | Un solo archivo no tiene carpeta de estilos |
| 6 | §6.3: cada reemplazo genera aviso | Avisan los quites, los `…` y `—` reemplazados y los dígitos. `[risa]` → `[laughter]` y `<strong>` no avisan | Son traducciones, no pérdidas; evita ruido |
| 7 | §9: `--idioma en` sin normalizar números | Los números, y las unidades de moneda o porcentaje (`$7.20`, `5%`), no se comparan: se quitan de los dos lados | Whisper escribe cifras y símbolos; sin normalizador de números en inglés daba falsos errores (ponytail: sin num2words) |
| 8 | §4 y §8: semilla y metadatos por toma | Además, cada bloque guarda su `semilla`, sus `avisos` y su `emocion` (en Chatterbox, `exaggeration` y `cfg_weight` efectivos). La toma guarda `master` y `evaluacion` | Reproducir y auditar una toma |
| 9 | (no está en el spec) bloque sin voz | Si el motor no produce voz para un bloque, se avisa y queda en `avisos` | OmniVoice devuelve un arreglo vacío cuando el texto no termina en puntuación |
| 10 | §11.1: un commit por fase | F1 y F2 están en un solo commit (`5c28fc5`) | Se confirmaron juntos; cada fase está verificada por separado |

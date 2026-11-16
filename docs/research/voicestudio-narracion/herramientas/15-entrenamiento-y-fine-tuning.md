# Entrenamiento y Fine-Tuning de OmniVoice

> Investigación del 2026-11-15. Cómo se afina OmniVoice con datos propios usando el código que VoiceStudio incluye (`omnivoice/training`, `examples/`): preparación de datos, configuración, requisitos y si conviene frente a la clonación zero-shot para social-videos. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

* **No es una función de la app.** VoiceStudio no tiene pantalla ni endpoint de entrenamiento: `rg 'fine-?tun|omnivoice.cli.train'` sobre `electron/src`, `frontend/src` y `backend/api` no encuentra nada. Lo que hay es el **código de entrenamiento del OmniVoice original (k2-fsa, Xiaomi, Apache-2.0)**, copiado en `omnivoice/` y `examples/` **(leída)**.
* **Qué entrena:** el modelo completo. `create_optimizer_and_scheduler` aplica `AdamW(self.model.parameters())` sobre todos los parámetros. El modelo se carga en **float32** con `attn_implementation="flex_attention"`. **No hay LoRA/PEFT ni gradient checkpointing** (`rg lora|peft|gradient_checkpoint omnivoice/` no da resultados) **(leída, `omnivoice/training/trainer.py` L160-165, `builder.py` L77-83)**.
* **Arquitectura que se ajusta:** backbone `Qwen/Qwen3-0.6B` + 8 codebooks de audio (`audio_vocab_size` 1025) del tokenizer `eustlb/higgs-audio-v2-tokenizer` **(leída, `examples/config/train_config_finetune.json`)**.
* **Herramientas:** `accelerate` (DDP o DeepSpeed ZeRO-2), TensorBoard, WebDataset (`uv sync --extra train`) **(leída, `docs/training.md`, `pyproject.toml` L229)**.

---

## 2. Cómo Se Usa

### Paso 1. Manifiesto JSONL

```jsonl
{"id": "clara_0001", "audio_path": "/abs/clara/0001.wav", "text": "Hoy te muestro cómo...", "language_id": "es"}
```

`id`, `audio_path` y `text` son obligatorios; `language_id` es opcional. El audio (wav/flac/mp3) se remuestrea a 24 kHz **(leída, `docs/data_preparation.md` §1)**. Para un modelo de hablantes fijos se agrega `"instruct": "<nombre>"` en cada línea (lo lee `omnivoice/data/processor.py` L99) **(leída)** y la configuración del paso 4.

### Paso 2 (opcional). Limpiar el audio con Sidon

```bash
python -m omnivoice.scripts.denoise_audio \
  --input_jsonl data.jsonl \
  --tar_output_pattern data/denoised/audios/shard-%06d.tar \
  --jsonl_output_pattern data/denoised/txts/shard-%06d.jsonl \
  --feature_extractor_path sidon_feature_extractor_cuda.pt \
  --decoder_path sidon_decoder_cuda.pt --target_sample_rate 24000 --batch_duration 200.0
```

Fuente: `docs/data_preparation_advanced.md` **(leída)**. Pesos en `sarulab-speech/sidon-v0.1`.

### Paso 3. Tokenizar a shards WebDataset

```bash
CUDA_VISIBLE_DEVICES=0 python -m omnivoice.scripts.extract_audio_tokens \
  --input_jsonl data/train.jsonl \
  --tar_output_pattern data/finetune/tokens/train/audios/shard-%06d.tar \
  --jsonl_output_pattern data/finetune/tokens/train/txts/shard-%06d.jsonl \
  --tokenizer_path eustlb/higgs-audio-v2-tokenizer --nj_per_gpu 1 --shuffle True
```

Genera `.npy` de forma `[8, T]` int16 y un `data.lst` (`<tar> <jsonl> <n> <segundos>`). `--min_num_shards` vale 32 por defecto **(leída, `data_preparation.md` §2)**. Repetir con el set `dev`.

### Paso 4. Configurar y lanzar

```bash
accelerate launch --gpu_ids "0" --num_processes 1 \
  -m omnivoice.cli.train \
  --train_config examples/config/train_config_finetune.json \
  --data_config examples/config/data_config_finetune.json \
  --output_dir exp/omnivoice_finetune
tensorboard --logdir exp/omnivoice_finetune/tensorboard
```

Esto es `examples/run_finetune.sh` adaptado a 1 GPU (el script trae `GPU_IDS="0,1"`, `NUM_GPUS=2`) **(leída)**. Para reanudar: `"resume_from_checkpoint": "exp/.../checkpoint-N"` **(leída, `docs/training.md`)**.

### Paso 5. Usar el checkpoint

En VoiceStudio: Settings → Models → TTS → OmniVoice → carpeta local con `config.json` + pesos + tokenizer, con metadatos de checkpoint OmniVoice ([14](14-modelos-y-hardware.md) §2.3) **(leída, `docs/local-model-folders.md`)**. Que el checkpoint de salida del trainer tenga exactamente ese formato **no verificado**.

---

## 3. Opciones y Parámetros

| Campo | Default en código | Receta de fine-tune | Para qué | Fuente |
| :--- | :--- | :--- | :--- | :--- |
| `init_from_checkpoint` | `None` | `"k2-fsa/OmniVoice"` | Parte de los pesos preentrenados | `config.py`; `train_config_finetune.json` **(leída)** |
| `steps` | 300 000 | **5 000** | Pasos totales | **(leída)** |
| `learning_rate` | 1e-4 | **5e-5** | LR pico (scheduler `cosine`) | **(leída)** |
| `warmup_ratio` | 0,03 | 0,01 | Calentamiento | **(leída)** |
| `batch_tokens` | 8192 | 8192 | Tokens por lote por GPU (el principal control de memoria) | **(leída)** |
| `gradient_accumulation_steps` | 1 | 1 | Acumulación de gradientes | **(leída)** |
| `prompt_ratio_range` | (0,0, 0,3) | (0,0, 0,3) | Fracción usada como "prompt" de clonación. `[0,0]` = sin clonación, hablantes por `instruct` | `config.py`; issue #19 **(leída)** |
| `instruct_ratio` | **1,0** | **0,0** | Uso del campo `instruct`. Con hablantes por nombre: 1,0 | issue #19 **(leída)** |
| `language_ratio` | 0,8 | 0,8 | Condicionar por idioma | **(leída)** |
| `mixed_precision` | `bf16` | `bf16` | Precisión mixta | **(leída)** |
| `use_deepspeed` / `deepspeed_config` | `False` | — | ZeRO-2 con `examples/config/ds_config_zero2.json` (sin *offload* a CPU) | `trainer.py` L110-120 **(leída)** |
| `save_steps` / `eval_steps` | 10 000 / 1 000 | 500 / 500 | Checkpoints y evaluación | **(leída)** |

---

## 4. Ejemplos

**Un hablante fijo con nombre** (sin referencia en inferencia), según el mantenedor en [k2-fsa/OmniVoice#19](https://github.com/k2-fsa/OmniVoice/issues/19) **(leída, B)**:

```json
{
  "init_from_checkpoint": "k2-fsa/OmniVoice",
  "prompt_ratio_range": [0.0, 0.0],
  "instruct_ratio": 1.0,
  "learning_rate": 5e-5,
  "steps": 5000
}
```

Cada línea del JSONL lleva `"instruct": "clara"`; en inferencia se pide `instruct="clara"`.

**Requisitos estimados** (cálculo propio, **no verificado**):

| Recurso | Estimación | Base |
| :--- | :--- | :--- |
| Parámetros | ~0,6 B (Qwen3-0.6B + cabezas de audio); Spheron indica 613 M | [spheron.network](https://www.spheron.network/tools/gpu-recommender/k2-fsa/OmniVoice/) **(snippet)** |
| VRAM del fine-tune completo | pesos fp32 (2,4 GB) + gradientes (2,4) + AdamW (4,9) ≈ **9,8 GB antes de activaciones** | 16 bytes/parámetro con AdamW y pesos maestros fp32 |
| ¿Cabe en la RTX 4060 de 8 GB? | **No**, sin cambios de código (Adam de 8 bits, gradient checkpointing u *offload* de DeepSpeed, que el repo no trae) | — |
| Tiempo de referencia | 2× H20, **~1 h** para la receta de 5000 pasos | mantenedor en #19 **(leída)** |
| Colab T4 | El T4 no tiene bf16 nativo y la receta usa `bf16` → probablemente falla o va lento | **no verificado** |

---

## 5. Tips y Trucos

* **La calidad de los datos es lo que cuenta.** Si el modelo empeora después del ajuste, "lo más probable es que los datos sean de baja calidad o los hiperparámetros inadecuados" (LR, pasos): revisar audio y transcripciones primero ([#193](https://github.com/k2-fsa/OmniVoice/issues/193)) **(leída, B)**.
* **¿Cuánto audio?** No hay cifra oficial. "Más datos es mejor" (#19); "unas pocas horas podrían bastar, hay que probar" ([#171](https://github.com/k2-fsa/OmniVoice/issues/171), estilo de habla) **(leída, B)**. Un usuario que agregó checheno estimó 20–40 h para un idioma nuevo ([#185](https://github.com/k2-fsa/OmniVoice/issues/185), título) **(snippet)**.
* **Para cada clip:** voz sola, sin cambios de hablante, con transcripción exacta. El modelo base cambia de voz a mitad de frase porque sus datos de entrenamiento traen cambios de hablante, y "esto no se arregla sin entrenar un modelo nuevo"; afinar con datos limpios "puede ayudar" ([#206](https://github.com/k2-fsa/OmniVoice/issues/206)) **(leída, B)**.
* **Ruido en la referencia:** el modelo base se entrenó con aumento de ruido en una fracción del *prompt* para tolerar referencias sucias (`extract_audio_tokens_add_noise`) **(leída, `data_preparation_advanced.md`)**.
* **conflicto (rutas):** `docs/training.md` y `examples/run_finetune.sh` usan `config/train_config_finetune.json`, pero los archivos están en `examples/config/`. Si se corre `bash examples/run_finetune.sh` desde la raíz, como indica `examples/README.md`, la ruta no existe. Hay que ajustar `TRAIN_CONFIG` y `data_config` **(leída)**.
* **conflicto (defaults):** `instruct_ratio` es 1,0 en `config.py`, pero la receta lo fija en 0,0. Un JSON que omita el campo hereda 1,0 **(leída)**.

---

## 6. Problemas Conocidos

| Problema | Estado | Fuente |
| :--- | :--- | :--- |
| El modelo afinado a veces genera artefactos o audio que no es habla | Cerrado: atribuido a los datos | [k2-fsa/OmniVoice#193](https://github.com/k2-fsa/OmniVoice/issues/193) **(leída)** |
| La voz cambia durante la generación (modelo base) | Cerrado sin arreglo; nueva versión con datos limpios "en unos meses" | [#206](https://github.com/k2-fsa/OmniVoice/issues/206) **(leída)** |
| Error al abrir el `.tar` al afinar en Windows | Cerrado con workaround | [#205](https://github.com/k2-fsa/OmniVoice/issues/205) **(leída)** |
| Falta el código para construir los datos multilingües (remuestreo, denoise, filtrado) | Abierto | [#244](https://github.com/k2-fsa/OmniVoice/issues/244) (título) **(snippet)** |
| **No hay licencia comercial posible para los pesos actuales**: "debido a restricciones no comerciales de los datos de entrenamiento, no tenemos los derechos" | Abierto; anuncian un modelo con licencia más abierta, sin fecha | [#235](https://github.com/k2-fsa/OmniVoice/issues/235), [#258](https://github.com/k2-fsa/OmniVoice/issues/258), [#275](https://github.com/k2-fsa/OmniVoice/issues/275), [#284](https://github.com/k2-fsa/OmniVoice/issues/284) **(leída, B)** |

---

## 7. Qué Dice la Comunidad

* **Mantenedor (B):** "el fine-tuning es muy rápido; un amplio rango de GPUs puede hacerlo" (#19). Choca con la estimación de memoria del §4 para 8 GB: **conflicto**. La frase "amplio rango" no especifica VRAM, y su receta usó H20 de 96 GB.
* **Licencias (B):** Emilia-Large mezcla Emilia (CC-BY-NC) con Emilia-YODAS (CC-BY). Entrenar solo con YODAS quitaría la restricción NC de los datos, pero **el tokenizer Higgs sigue imponiendo restricciones comerciales** ([licencia de bosonai](https://huggingface.co/bosonai/higgs-audio-v2-tokenizer/blob/main/LICENSE)) (#235) **(leída)**.
* **Guías de terceros (C):** recomiendan LoRA o QLoRA para evitar OOM al afinar ([theneuralbase](https://theneuralbase.com/huggingface-fine-tuning/learn/beginner/oom-reduce-batch-or-use-qlora/)). Es un consejo genérico que el código de OmniVoice no soporta **(snippet)**.

---

## 8. Qué Sirve para social-videos

**Veredicto: no vale la pena un fine-tuning de OmniVoice con la voz del usuario.** Razones, de más a menos fuerte:

1. **Licencia.** Los pesos base son **CC-BY-NC**, y un modelo afinado es una obra derivada: sigue siendo no comercial. Además el tokenizer Higgs tiene sus propios términos. Para **publicidad** o canales monetizados, el resultado no se puede usar, igual que con zero-shot. El mantenedor dice explícitamente que no puede dar licencia comercial (#235) **(leída)**.
2. **Hardware.** El trainer hace un ajuste completo en fp32 + AdamW sin LoRA ni checkpointing: se estiman ~10 GB más activaciones. **No cabe en la RTX 4060 de 8 GB** sin modificar el código (**no verificado** empíricamente). Habría que alquilar una GPU de 24 GB o más.
3. **Ganancia incierta frente a zero-shot.** Para un solo hablante, la clonación con 8–12 s de referencia limpia ([11](../11-audio-de-referencia.md)) ya transfiere timbre y entrega. Afinar ayuda sobre todo a la estabilidad (menos cambios de voz, #206) y a idiomas o acentos poco cubiertos. La pronunciación inconsistente entre generaciones es un problema abierto ([#237](https://github.com/k2-fsa/OmniVoice/issues/237), solo el título) **(snippet)**, y no está demostrado que el fine-tuning lo resuelva. El español latino neutro ya está cubierto.
4. **Costo de datos.** "Unas pocas horas" de audio limpio y transcrito de una sola voz, más un set dev, frente a los 8–12 s por estilo que pide la clonación.

**Cuándo reconsiderarlo:** cuando k2-fsa publique el modelo "con licencia más abierta" (#235) y haya un uso que zero-shot no resuelva: inestabilidad de voz medida en lotes largos, o una pronunciación que no se corrige con el guion. En ese caso, conviene evaluar primero el ajuste de un motor con licencia comercial (Qwen3-TTS, Apache-2.0, ya en `narration/`). Que tenga receta oficial de fine-tuning **no verificado** en esta sesión.

**Qué sí se puede copiar ya:** la disciplina de datos de esta receta (JSONL con `id`/`audio_path`/`text`/`language_id`, transcripción exacta, un hablante por clip, sin denoise agresivo en la referencia). Es el mismo formato que conviene para la biblioteca de voces de `narration/voz/`.

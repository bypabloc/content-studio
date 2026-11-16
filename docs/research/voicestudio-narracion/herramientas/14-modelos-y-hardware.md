# Modelos y Hardware

> Investigación del 2026-11-15. Cómo gestiona VoiceStudio los modelos (Model Catalogue, descargas, carpetas locales, disco), cómo detecta y usa la GPU, qué ajustes sirven para 8 GB de VRAM y cómo correr el backend en una GPU remota. Índice en [README.md](README.md). Marcas: **(leída)**, **(snippet)**, **no verificado**, **conflicto**; comunidad A/B/C ([01](../01-metodo-y-fuentes.md) §3).

---

## 1. Qué Es

| Pieza | Qué hace | Fuente |
| :--- | :--- | :--- |
| **Model Catalogue** | Lista de motores y pesos con tamaño, estado ("In memory"), botón de instalar, cancelar y descargar, y desglose de disco antes de instalar | `docs/downloading-models.md`, `docs/engines/disk-usage.md` **(leída)** |
| **`backend/config/models.yaml`** | Fuente de verdad del catálogo: `repo_id`, `size_gb`, `curated_on` (recomendado por host: `cuda`, `cpu`, …), `required` | **(leída)** |
| **Descargas remotas** | Hugging Face Hub con descargador segmentado propio (8 rangos de 16 MB, reanudable, verifica SHA) y espejo automático `hf-mirror.com` | `docs/downloading-models.md` **(leída)** |
| **Carpetas locales** | Usar un checkpoint ya descargado (solo OmniVoice y MLX-Audio) | `docs/local-model-folders.md` **(leída)** |
| **GPU Auto-Detect** | Detecta `cuda`/`rocm`/`xpu`/`mps`/`cpu`, muestra una insignia por motor ("GPU active", "CPU fallback") y avisa antes de un render lento | `docs/performance.md` L31-51, `backend/core/device_caps.py` **(leída)** |
| **GPU remota** | El backend corre en otra máquina y la app es cliente, vía Tailscale + API key | `docs/remote-gpu.md` **(leída)** |
| **Benchmarks** | Arnés `scripts/bench_pipeline.py` (RTF y pico de VRAM) | `docs/benchmarks.md` **(leída)** |

**Tamaños de descarga de los motores relevantes** (`models.yaml`, `size_gb`) **(leída)**:

| Motor | Repo | GiB | Recomendado en |
| :--- | :--- | :--- | :--- |
| OmniVoice (default, requerido) | `k2-fsa/OmniVoice` | 2,4 | todos |
| VoxCPM2 | `openbmb/VoxCPM2` | 5,0 | cuda |
| CosyVoice 3 0.5B | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` | 9,8 | cuda |
| Ming-3.0-tts 0.5B | `inclusionAI/Ming-3.0-tts-0.5b` | 2,8 | solo CUDA |
| Whisper large-v3 (faster-whisper) | `Systran/faster-whisper-large-v3` | 2,9 | cuda, cpu |
| OmniVoice GGUF | `Serveurperso/OmniVoice-GGUF` | Q8_0 ~0,95 / BF16 ~1,6 / F32 ~3,2 | — |

---

## 2. Cómo Se Usa

### 2.1 Elegir motor

* **UI:** Model Catalogue, o <kbd>Ctrl</kbd>+<kbd>E</kbd> para cambiar rápido. **Env:** `OMNIVOICE_TTS_BACKEND=omnivoice` (la variable gana sobre la UI) **(leída, `docs/engines/README.md`)**.
* `GET /setup/recommendations` devuelve las sugerencias "best for your system" según `curated_on` **(leída, `backend/api/routers/setup/models.py` L634)**.
* `GET /engines` reporta por motor `max_ref_seconds` y `ref_strategy` **(leída, `docs/engines/README.md`)**.

### 2.2 Instalar pesos antes del primer uso

El primer `generate` descarga ~2,3 GB y esa descarga **cuenta contra el presupuesto de 300 s**: en un T4 nuevo la primera petición falló por timeout con la GPU ociosa **(leída, `docs/hardware-notes-tesla-t4.md`)**. Conviene instalar antes:

```bash
curl -X POST http://127.0.0.1:3900/models/install \
  -H 'Content-Type: application/json' -d '{"repo_id": "k2-fsa/OmniVoice"}'
# progreso por SSE en /setup/download-stream
```

### 2.3 Usar una carpeta local (evitar descargar dos veces)

Settings → Models → TTS → fila del motor → elegir carpeta (o **Discover** sobre una carpeta padre, que revisa hasta 100 subcarpetas). La carpeta debe tener `config.json`, pesos `.safetensors`/`.bin` y el tokenizer. **No se aceptan symlinks**, y un fallo nunca dispara una descarga automática. Solo funciona con backend local **(leída, `docs/local-model-folders.md`)**.

Alternativa global: `HF_HOME` / `HF_HUB_CACHE`, o Settings → Storage (`OMNIVOICE_CACHE_DIR`) **(leída, `downloading-models.md`, `electron-storage.md`)**.

### 2.4 Liberar memoria sin reiniciar

```bash
curl -X POST "http://127.0.0.1:3900/system/flush-memory"                    # vacía cachés
curl -X POST "http://127.0.0.1:3900/system/flush-memory?unload_model=true"  # + descarga el TTS
curl "http://127.0.0.1:3900/model/loaded"                                   # qué está residente
curl -X POST "http://127.0.0.1:3900/model/unload/tts"
```

Fuente: `docs/performance.md` L237-243 **(leída)**. No libera un trabajo que acaba de vencer: el hilo sigue ocupando VRAM hasta terminar.

### 2.5 GPU remota (backend en otra máquina)

```bash
# En la máquina con GPU
export OMNIVOICE_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
export OMNIVOICE_SERVER_MODE=1
uv run uvicorn backend.main:app --host 0.0.0.0 --port 3900
tailscale serve 3900          # TLS dentro de la tailnet
```

En la app: Settings → Sharing → **Remote backend** → URL MagicDNS + API key → *Test connection* → *Save & reload*. Desde un navegador: `https://gpu-box.<tailnet>.ts.net/#api_key=<key>` (fragmento `#`, que no llega a los logs). **No usar `tailscale funnel`** **(leída, `docs/remote-gpu.md`)**. Variante sin hardware propio: el notebook de Colab levanta el backend completo en un T4 gratuito **(leída, `notebooks/OmniVoice_Studio_Colab.ipynb`)**.

### 2.6 Medir

```bash
uv run python scripts/bench_pipeline.py tts   # con la app cerrada
```

Imprime RTF en caliente (<1 = más rápido que tiempo real) y pico de VRAM en CUDA **(leída, `docs/benchmarks.md`)**.

---

## 3. Opciones y Parámetros

| Variable | Default | Para qué | Fuente |
| :--- | :--- | :--- | :--- |
| `OMNIVOICE_DEVICE` | `auto` | Fijar `cuda`/`rocm`/`xpu`/`mps`/`cpu`; se ignora si el host no lo tiene | `performance.md` L89; `device_caps.py` L739-749 **(leída)** |
| `CUDA_VISIBLE_DEVICES` | todas | Elegir GPU en multi-GPU | L91 **(leída)** |
| `OMNIVOICE_GPU_WORKERS` | auto (1 por cada 5 GB libres, máx. 4) | Generaciones concurrentes. **No subir en ≤10 GB** (#567) | L100; `model_manager.py` L111-117 **(leída)** |
| `OMNIVOICE_FREE_VRAM_BEFORE_GENERATE` | `auto` | Libera VRAM ociosa antes de generar si quedan <2 GB libres | L104 **(leída)** |
| `OMNIVOICE_LOW_MEMORY_HEADROOM_GB` | 2 | Umbral de "Low GPU memory" | L104 **(leída)** |
| `OMNIVOICE_OFFLOAD_AFTER_GENERATION` | off | Mueve el modelo a RAM tras generar (útil si se comparte la GPU) | L95, L267-297 **(leída)** |
| `OMNIVOICE_IDLE_TIMEOUT_S` | 900 | Descarga el TTS tras inactividad (~8 s para recargar) | L94 **(leída)** |
| `OMNIVOICE_SINGLE_ENGINE_RESIDENT` | 1 | Un solo motor TTS en memoria | L102 **(leída)** |
| `OMNIVOICE_FLASHINFER` | 0 | ~2× en decodificación, pero suma ~½ del peso del LLM en VRAM: **apagado en tarjetas justas** | L92 **(leída)** |
| `TORCH_COMPILE_DISABLE=1` | — | Desactiva `torch.compile` (útil si falla Triton) | L113 **(leída)** |
| `OMNIVOICE_GENERATE_TIMEOUT_S` | 300 | Presupuesto de cómputo por generación (+1 s cada 40 caracteres tras 1200) | L107 **(leída)** |
| `OMNIVOICE_PROMPT_DISK_CACHE` | 1 | Cachea referencias codificadas (~10 KB por voz, 32 voces) | L93 **(leída)** |
| `OMNIVOICE_GGUF_QUANT` | `auto` | `Q4_K_M` / `Q8_0` / `BF16` / `F32` | `docs/engines/omnivoice-gguf.md` **(leída)** |
| `OMNIVOICE_SEGMENTED_DOWNLOAD` | on | `0` = descarga en un solo flujo | `downloading-models.md` **(leída)** |
| `HF_ENDPOINT` / `OMNIVOICE_HF_ENDPOINT_MODE=manual` | auto | Espejo de HF | **(leída)** |
| `UV_LINK_MODE=hardlink` | — | Garantiza deduplicar los venvs de *sidecars* en ext4 | `docs/engines/disk-usage.md` **(leída)** |
| *Speed / quality* (Settings) | — | `num_step`: Fast 8, Balanced 16, Quality 32, Max 64 (solo OmniVoice) | `hardware-notes-tesla-t4.md` **(leída)** |

---

## 4. Ejemplos

**Perfil para RTX 4060 Laptop 8 GB** (deducido de los defaults; **no verificado** en esa GPU):

```bash
# ~/.config/omnivoice/env
OMNIVOICE_DEVICE=cuda
OMNIVOICE_GPU_WORKERS=1                 # explícito; es lo que haría el auto con 8 GB
OMNIVOICE_FREE_VRAM_BEFORE_GENERATE=always
OMNIVOICE_FLASHINFER=0
OMNIVOICE_SINGLE_ENGINE_RESIDENT=1
OMNIVOICE_IDLE_TIMEOUT_S=3600           # trabajo por ráfagas: evita recargar
```

**Qué cabe en 8 GB** (cifras del repo; la RTX 4060 no está medida):

| Motor | VRAM declarada o medida | ¿Cabe en 8 GB? | Fuente |
| :--- | :--- | :--- | :--- |
| OmniVoice | Piso **6 GB** (único motor con piso); pico **2,05 GB** (`max_memory_allocated`) / 2,49 GB (`nvidia-smi`) en T4 sin Whisper | Sí, si no se carga Whisper al mismo tiempo | `tts_backend.py` L1897; `hardware-notes-tesla-t4.md` **(leída)** |
| OmniVoice GGUF | Q8_0 ~945 MB para 4–12 GB | Sí, holgado | `omnivoice-gguf.md` **(leída)** |
| VoxCPM2, IndexTTS 2.5, CosyVoice 3 | Sin piso declarado ("inventarlo pondría un número sin respaldo") | **no verificado** | `tts_backend.py` L1890-1896 **(leída)** |
| OmniVoice + Whisper large-v3 | OOM en 8 GB al clonar sin transcripción | No; dar la transcripción | issue #282 (ver [11](../11-audio-de-referencia.md) §2) |

---

## 5. Tips y Trucos

* **La primera generación siempre es lenta** (carga ~8 s más compilación). Medir desde la segunda **(leída, `performance.md` L22-24)**.
* **Un perfil de voz sin transcripción** lanza Whisper en cada uso. En 8 GB eso suma VRAM y puede producir OOM: escribirla siempre **(leída, L12-21)**.
* **Revisar que no esté en CPU sin avisar:** Settings → Performance → *Device & compute*, `/system/diagnose` o la insignia por motor **(leída, L31-51)**.
* **Si la VRAM se desborda a la memoria compartida, todo va varias veces más lento**: es la misma regla 2 de `AGENTS.md` de este repo. VoiceStudio lo previene con `FREE_VRAM_BEFORE_GENERATE=auto` y presupuesta como CPU a una GPU bajo el piso **(leída, L104, L127)**.
* **Torch duplicado entre venvs:** un *sidecar* con otro build de torch suma varios GB. uv deduplica por *wheel* idéntica solo si la caché y el venv están en el mismo filesystem **(leída, `disk-usage.md`)**. **Medido aquí:** `du -sh narration/.venv-*` da chatterbox 6,0G, omnivoice 6,0G, qwen 5,9G y voxcpm **749M** (los archivos ya contados por hardlink no se repiten), así que la deduplicación ya funciona en este ext4.
* **conflicto (menor):** `disk-usage.md` dice que uv usa `clone` en Linux. La salida de `uv pip install --help` (uv 0.9.26) no muestra el default, y la medición anterior apunta a *hardlinks*. En ext4 no hay reflink, así que `UV_LINK_MODE=hardlink` es la opción segura.
* **Instalación:** necesita el tamaño de la descarga **+ 2 GB libres** **(leída, `downloading-models.md`)**.
* **Xet desactivado a propósito** (`HF_HUB_DISABLE_XET=1`) para tener progreso por byte; `HF_HUB_DISABLE_XET=0` lo reactiva **(leída)**.

---

## 6. Problemas Conocidos

| Problema | Estado | Fuente |
| :--- | :--- | :--- |
| En tarjetas de 4 GB (GTX 1650 Ti, Quadro P2000) OmniVoice pagina a RAM y tarda minutos | Origen del piso de 6 GB | [#1226](https://github.com/debpalash/VoiceStudio/issues/1226), [#1222](https://github.com/debpalash/VoiceStudio/issues/1222) **(leída, `engines/omnivoice.md`)** |
| Dos generaciones concurrentes sobrecomprometían la VRAM en tarjetas de 8 GB | Resuelto: workers presupuestados a 5 GB | [#567](https://github.com/debpalash/VoiceStudio/issues/567) **(leída, `model_manager.py` L111)** |
| La verificación previa de VRAM de PyTorch-Whisper forzaba CPU en GPUs de 6–8 GB aunque estuvieran libres | Cerrado | [#2041](https://github.com/debpalash/VoiceStudio/issues/2041) (título vía `gh`) **(snippet)** |
| El chequeo de RAM bloqueaba equipos con 8 GB de RAM (Windows reporta ~7,8) | Cerrado | [#1618](https://github.com/debpalash/VoiceStudio/issues/1618) **(snippet)** |
| Un dub abortado dejaba el TTS en CPU (10–50× más lento) | Resuelto en v0.3.23 | [#1191](https://github.com/debpalash/VoiceStudio/issues/1191) **(leída, `performance.md`)** |
| CUDA graphs mataban el backend en Turing (T4) | Resuelto: modo `default` bajo sm_80. La RTX 4060 (Ada, sm_89) usa `reduce-overhead` | [#2135](https://github.com/debpalash/VoiceStudio/issues/2135) **(leída)** |
| **conflicto:** la nota del T4 dice que 2,5 GB queda "dentro del tier mínimo de 4 GB", pero el código declara un piso de **6 GB** | Documentación desalineada | `hardware-notes-tesla-t4.md` vs `tts_backend.py` L1897 **(leída)** |
| **La tabla de benchmarks está vacía** ("No verified rows yet"): no hay RTF publicados por GPU | Abierto | `docs/benchmarks.md` **(leída)** |

---

## 7. Qué Dice la Comunidad

* Una guía de terceros recomienda "NVIDIA con 8 GB+ de VRAM" para los motores de más calidad ([besthub.dev](https://www.besthub.dev/articles/voicestudio-local-first-open-source-voice-platform-for-cloning-dubbing-tts-8315f8ed2488)) **(snippet, C)**.
* Un issue del repo upstream describe OmniVoice como "pesado" para usar en el dispositivo, ~4 GB de VRAM en laptop ([k2-fsa/OmniVoice#69](https://github.com/k2-fsa/OmniVoice/issues/69)) **(snippet, B)**. Un usuario de pyVideoTrans tuvo OOM en una tarjeta de 8 GB durante la generación ([bbs.pyvideotrans.com](https://bbs.pyvideotrans.com/show/5814)) **(snippet, C)**.
* Las estimaciones de VRAM de Spheron ([spheron.network](https://www.spheron.network/tools/gpu-recommender/k2-fsa/OmniVoice/)) difieren de las de [spheron.ai](https://www.spheron.ai/tools/gpu-recommender/k2-fsa/OmniVoice/) (~1,3 GB en FP16): **conflicto**, y ninguna es una medición **(snippet, C)**.

---

## 8. Qué Sirve para social-videos

1. **Para 8 GB, OmniVoice cabe** si se cumplen dos condiciones: un solo modelo en GPU (ya es regla del repo) y **transcripción siempre presente** para no cargar Whisper. Un pico de ~2–2,5 GB deja margen; el piso de 6 GB de VoiceStudio es conservador y está pensado para incluir Whisper co-cargado.
2. **Copiar tres ideas a `narration/tts.py`:**
   * **Aviso previo** cuando la VRAM libre es <2 GB (`torch.cuda.mem_get_info()`), antes de generar, en vez de descubrirlo por lentitud.
   * **Caché de la referencia codificada** por hash del WAV (VoiceStudio guarda ~10 KB por voz en `prompt_cache/`), para no recodificar en cada lote.
   * **Medir RTF y pico de VRAM** por motor con un script como `bench_pipeline.py`, para llenar la tabla que VoiceStudio tiene vacía, al menos para la RTX 4060.
3. **Instalar pesos antes de la primera corrida larga**: el primer `generate` mezcla descarga y cómputo, y el tiempo engaña.
4. **GPU remota:** solo vale la pena para motores grandes (CosyVoice 3 de 9,8 GB, MOSS 8B). El patrón Tailscale + API key es reutilizable con cualquier servidor; no hace falta VoiceStudio.
5. **Disco:** los cuatro venvs de `narration/` ya deduplican por *hardlinks*. Mantener `UV_CACHE_DIR` en el mismo disco y fijar el mismo build de torch donde los motores lo permitan.

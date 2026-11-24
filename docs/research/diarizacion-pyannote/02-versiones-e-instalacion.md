# 02. Versiones e instalación

## 1. Versiones de pyannote.audio (leída, [PyPI](https://pypi.org/pypi/pyannote.audio/json) y [CHANGELOG](https://github.com/pyannote/pyannote-audio/blob/develop/CHANGELOG.md))

| Versión | Fecha | Python | Qué cambia para nosotros |
| :--- | :--- | :--- | :--- |
| 4.0.0 | 2025-09-29 | ≥ 3.10 | community-1, VBx, salida exclusiva, uso offline. La E/S pasa de torchaudio a **torchcodec**. `use_auth_token` pasa a `token` y `PYANNOTE_CACHE` deja de usarse |
| 4.0.1 | 2025-10-10 | ≥ 3.10 | Avisa (en vez de fallar) ante argumentos no soportados |
| 4.0.2 | 2025-11-19 | ≥ 3.10 | **Fija `torch==2.8.0`**, torchcodec y torchaudio para evitar un *segfault*. Agrega `Pipeline.cuda()` y `preload` |
| 4.0.3 | 2025-12-07 | ≥ 3.10 | Soporte de lightning 2.6+ |
| 4.0.4 | 2026-02-07 | ≥ 3.10 | **Relaja la fijación de torch** |
| 4.0.5 | 2026-06-22 | ≥ 3.10 | Menos paquetes de telemetría |
| 4.0.6 | 2026-06-29 | — | **Retirada (yanked)**: `Pipeline.__call__` devolvía un generador y rompía WhisperX ([#2032](https://github.com/pyannote/pyannote-audio/issues/2032)) |
| 4.0.7 | 2026-06-30 | ≥ 3.10 | Inferencia por lotes (secuencial) y `subfolder` en `from_pretrained` |
| 4.1.0 | 2026-11-17 | **≥ 3.11** | Se quita Python 3.10. Corrige que VBx fallara al pedir más hablantes que embeddings, y que el DER desbordara en float16 con grabaciones largas |
| **4.1.1** | 2026-11-19 | ≥ 3.11 | Fix de entrenamiento. **Última versión** |

* **Recomendado**: `4.1.1` en un venv con Python 3.12, como el resto de los motores (`faster-whisper.json`, `qwen-0.6b.json`). La regla de Python 3.10 mínimo es para `server/src/`, no para el venv de cada motor.
* **Si hiciera falta Python 3.10**: `4.0.7`. Nunca `4.0.6`.

### Dependencias de 4.1.1 (leída, PyPI)

`torch>=2.8.0`, `torchaudio>=2.8.0`, `torchcodec>=0.7.0`, `huggingface-hub>=0.28.1`, `lightning>=2.4`, `pyannote-core>=6.1.0`, `pyannote-pipeline>=4.1.0`, `pyannote-database>=6.3.0`, `pyannote-metrics>=4.2.0`, `pyannoteai-sdk>=0.3.0`, `opentelemetry-*`, `matplotlib`, `asteroid-filterbanks`, `torch-audiomentations`, `pytorch-metric-learning`, `safetensors` y `rich`, entre otras. El paquete pesa poco, pero torch con CUDA ocupa varios GB.

* `pyannote-core>=6.0.1` es necesario para iterar `for turn, speaker in annotation`. Con 5.x da `TypeError: 'int' object is not subscriptable` ([#1928](https://github.com/pyannote/pyannote-audio/issues/1928), leída). Con 4.1.1 queda cubierto.

## 2. torchcodec: la pieza delicada

Desde 4.0, pyannote decodifica audio con [torchcodec](https://github.com/meta-pytorch/torchcodec), que usa las **bibliotecas compartidas de FFmpeg** instaladas en el sistema.

### Compatibilidad torch ↔ torchcodec (leída, README de torchcodec)

| torchcodec | torch | Python |
| :--- | :--- | :--- |
| 0.14 a 0.17 (0.17.0, 2026-09-30) | ≥ 2.11 | 3.10 a 3.14 |
| 0.11 | 2.11 | 3.10 a 3.14 |
| 0.10 | 2.10 | 3.10 a 3.14 |
| 0.9 | 2.9 | 3.10 a 3.14 |
| 0.8 | 2.9 | 3.10 a 3.13 |
| 0.7 | 2.8 | 3.9 a 3.13 |

* Una pareja incompatible (torchcodec 0.8 con torch 2.8) produce el *segfault* que llevó a fijar versiones en 4.0.2 ([#1976](https://github.com/pyannote/pyannote-audio/issues/1976), leída).
* **torchcodec ≥ 0.14** corrige una búsqueda dentro del archivo que hacía crecer la etapa de embeddings de forma cuadrática con la duración ([#1955](https://github.com/pyannote/pyannote-audio/issues/1955), leída). Ver [05](05-rendimiento-y-vram.md).
* En Windows, `pip install torchcodec` instala ruedas **solo para CPU**, lo que basta para decodificar audio (leída, README).

### FFmpeg en Windows

* torchcodec soporta FFmpeg 4 a 9 y en Windows necesita el build **shared** (con DLL separadas: `avcodec`, `avformat`, `avutil`…). Un `ffmpeg.exe` estático en el PATH no alcanza (leída, README de torchcodec).
* Síntoma típico: `RuntimeError: Could not load libtorchcodec`, con un intento fallido por cada versión de FFmpeg ([torchcodec#1006](https://github.com/meta-pytorch/torchcodec/issues/1006), leída por el agente; [#1940](https://github.com/pyannote/pyannote-audio/issues/1940), leída).
* Soluciones reportadas: registrar la carpeta de las DLL con `os.add_dll_directory(...)` antes de importar, o instalar FFmpeg desde conda-forge (snippet).
* **Para nosotros**: si el audio se pasa ya cargado en memoria, pyannote no necesita decodificar con torchcodec ([03](03-api-y-uso.md) §4). **no verificado**: si `import pyannote.audio` carga las DLL de torchcodec al importar. Hay que probarlo con el FFmpeg que detecta la app ([09](09-propuesta-para-content-studio.md)).

## 3. Receta propuesta (propuesta, no ejecutada)

Mismo formato que [qwen-0.6b.json](../../../server/src/content_studio/engines/recipes/qwen-0.6b.json):

```json
{
  "engine": "pyannote-community-1",
  "family": "diarization",
  "license": "MIT (código) / CC-BY-4.0 (pesos)",
  "steps": [
    {"kind": "python", "version": "3.12"},
    {"kind": "venv", "path": ".venv-diarize"},
    {"kind": "pip", "packages": ["torch==2.11.0+cu128", "torchaudio==2.11.0+cu128"], "index": "https://download.pytorch.org/whl/cu128"},
    {"kind": "pip", "packages": ["pyannote.audio==4.1.1", "torchcodec==0.17.0"]},
    {"kind": "hf", "repo": "pyannote/speaker-diarization-community-1", "revision": "<sha fijado>", "into": "hf"},
    {"kind": "verify", "import": "pyannote.audio"}
  ]
}
```

* torch 2.11 con cu128 es la combinación que ya usa el repo para Qwen. torchcodec 0.17 pide torch ≥ 2.11.
* El paso `hf` del repositorio restringido necesita el token del usuario: hay que revisar si el instalador de recetas ya lo soporta (pendiente de la spec).
* Se fija la `revision` (un commit) del repositorio de pesos, como en las otras recetas. Así se evita cargar un `config.yaml` que cambie después ([07](07-licencias-privacidad-y-seguridad.md) §5).
* Los valores `size_gb` y `vram_gb` se completan después de medir.

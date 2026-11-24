# 03. API y uso

Fuentes: [README](https://github.com/pyannote/pyannote-audio/blob/develop/README.md), [`speaker_diarization.py`](https://github.com/pyannote/pyannote-audio/blob/develop/src/pyannote/audio/pipelines/speaker_diarization.py) y [`core/pipeline.py`](https://github.com/pyannote/pyannote-audio/blob/develop/src/pyannote/audio/core/pipeline.py) en `develop` (leídas el 2026-11-24).

## 1. Ejemplo mínimo (leída, README)

```python
import torch
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1",
    token="HUGGINGFACE_ACCESS_TOKEN")        # 4.x: `token`, ya no `use_auth_token`
pipeline.to(torch.device("cuda"))            # o pipeline.cuda() desde 4.0.2

with ProgressHook() as hook:
    output = pipeline("audio.wav", hook=hook)

for turn, speaker in output.speaker_diarization:
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s {speaker}")
```

* Por defecto corre en **CPU**. `.to()` exige un `torch.device` y lanza `TypeError` si recibe un string. `.cuda()` acepta `None`, un `int` o un `torch.device` (leída, `core/pipeline.py`).
* Las etiquetas son `SPEAKER_00`, `SPEAKER_01`…, numeradas por orden de aparición en `labels()` (leída, `classes()`).

## 2. La salida: `DiarizeOutput` (leída)

```python
@dataclass
class DiarizeOutput:
    speaker_diarization: Annotation            # diarización normal (con solapes)
    exclusive_speaker_diarization: Annotation  # sin turnos solapados, pensada para transcripción
    speaker_embeddings: np.ndarray | None      # (num_speakers, dim), en el orden de speaker_diarization.labels()
```

* **Cómo se calcula la salida exclusiva**: después del clustering, el conteo de hablantes simultáneos se limita a 1 (`np.minimum(count.data, 1)`) y la diarización se reconstruye con ese conteo. En cada instante queda solo el hablante más probable, con las mismas etiquetas que la normal (leída, `apply`).
* `output.serialize()` devuelve un dict listo para JSON (leída):

```python
{"diarization": [{"start": 6.665, "end": 7.165, "speaker": "SPEAKER_00"}, ...],
 "exclusive_diarization": [{"start": 6.665, "end": 7.165, "speaker": "SPEAKER_00"}, ...]}
```

  Es el formato que conviene escribir en disco desde el venv del motor: el servidor lo lee con stdlib, sin pyannote.
* Si no hay voz en todo el audio, devuelve anotaciones vacías y `speaker_embeddings` de forma `(0, dim)`, sin error (leída).
* Con `legacy=True` devuelve solo el `Annotation`, como en 3.x.
* Iteración alternativa, compatible con cualquier `pyannote.core`: `for turn, _, speaker in annotation.itertracks(yield_label=True)`.
* RTTM: `Annotation` de pyannote.core tiene `write_rttm(file)` (**no verificado** en 6.x). Para nosotros alcanza con `serialize()`.

## 3. Número de hablantes (leída, `apply`)

```python
pipeline(audio, num_speakers=2)                    # exacto, si se conoce
pipeline(audio, min_speakers=2, max_speakers=5)    # rango
```

* `min_speakers` y `max_speakers` no tienen efecto si se da `num_speakers`.
* Si el número detectado queda fuera del rango (un audio demasiado corto para `min_speakers`), solo **avisa** con `warnings` y sigue.
* El conteo de hablantes simultáneos se recorta a `max_speakers`.
* Argumentos desconocidos se ignoran con un aviso: un error de tipeo no falla (desde 4.0.1).
* Fijar el número cuando se conoce es lo que más evita fusionar dos voces en una (VoiceStudio, [nota anterior](../voicestudio-narracion/herramientas/07-diarizacion.md) §5).

## 4. Audio en memoria y `preload` (leída)

```python
waveform = torch.from_numpy(samples).unsqueeze(0)   # (canal, tiempo), float32
output = pipeline({"waveform": waveform, "sample_rate": 16000})
# o bien, a partir de un archivo:
output = pipeline("audio.wav", preload=True)        # lo carga entero en memoria antes de procesar
```

* La entrada esperada es mono a 16 kHz: el estéreo se mezcla y otras frecuencias se remuestrean (leída, tarjeta del modelo). Desde 4.1.0 la mezcla depende de una política de canal por archivo (`channel`) y desaparece `Audio(mono=...)` (leída, release 4.1.0).
* `preload=True` falla si el dict ya trae `waveform` (leída, `prepare_one`).
* **Por qué importa**: cargar en memoria acelera la etapa de embeddings hasta 21× y evita el error en archivos cortos ([05](05-rendimiento-y-vram.md), [08](08-problemas-conocidos.md)).
* **Propuesta para el proyecto**: convertir con el FFmpeg que ya usa la app a WAV PCM de 16 bits, mono y 16 kHz, y leerlo con `wave` (stdlib) y `numpy.frombuffer`. No hacen falta soundfile ni torchcodec para decodificar.

## 5. Progreso (leída, `apply` y `whisperx/diarize.py`)

El `hook` se llama como `hook(step_name, step_artifact, file=..., total=..., completed=...)`. Las etapas son `segmentation`, `speaker_counting`, `embeddings` y `discrete_diarization`. Las largas llaman varias veces con `completed` y `total`.

WhisperX convierte eso en un porcentaje monótono: segmentación de 0 a 50 % y embeddings de 50 a 99 %. Sirve para alimentar la barra de la cola de trabajos:

```python
RANGES = {"segmentation": (0.0, 50.0), "embeddings": (50.0, 99.0)}
def hook(step_name, step_artifact, file=None, total=None, completed=None):
    if total and completed is not None:
        lo, hi = RANGES.get(step_name, (0.0, 99.0))
        report(lo + min(completed / total, 1.0) * (hi - lo))
```

## 6. Uso offline (leída, CHANGELOG 4.0.0)

1. Aceptar las condiciones de `pyannote/speaker-diarization-community-1` en Hugging Face.
2. Descargar el repositorio completo (`git lfs install` y `git clone https://hf.co/pyannote/speaker-diarization-community-1 <carpeta>`, con el token como contraseña), o con `huggingface_hub.snapshot_download(repo_id, revision=..., token=..., local_dir=...)`.
3. Cargar desde la carpeta, sin red y sin token:

```python
pipeline = Pipeline.from_pretrained(r"C:\...\engines\pyannote-speaker-diarization-community-1")
```

* El repositorio trae las subcarpetas `segmentation`, `embedding` y `plda`, y el pipeline las referencia como `$model/<subcarpeta>` (leída, `expand_subfolders` y los valores por defecto de `SpeakerDiarization`).
* Desde 4.0, la caché es la de `huggingface_hub` (`HF_HOME` o `HF_HUB_CACHE`) y `PYANNOTE_CACHE` no se usa. Antes de 4.0, `PYANNOTE_CACHE` pisaba `HF_HUB_CACHE` ([#2034](https://github.com/pyannote/pyannote-audio/issues/2034), leída).
* Para un trabajo de la app se recomienda **cargar siempre desde la carpeta local** dentro de `paths.engines_dir()`, y fijar `HF_HUB_OFFLINE=1` en el proceso para que nunca descargue durante un trabajo (la misma práctica que VoiceStudio).

## 7. Hiperparámetros (leída)

Constructor de `SpeakerDiarization` (los valores del `config.yaml` de community-1 pueden ser otros; ese archivo pide sesión):

| Parámetro | Por defecto en el código | Para qué |
| :--- | :--- | :--- |
| `segmentation_step` | 0.1 | Paso de la ventana de segmentación como fracción de su duración (90 % de solape) |
| `segmentation_batch_size` | 1 | Lote de la segmentación. Se puede cambiar después con su *setter* |
| `embedding_batch_size` | 1 | Lote de embeddings. **Controla el pico de VRAM** ([05](05-rendimiento-y-vram.md)) |
| `embedding_exclude_overlap` | False | Excluir el habla solapada al calcular embeddings |
| `clustering` | `VBxClustering` | También hay aglomerativo y k-means. k-means **exige** `num_speakers` |

Parámetros que se ajustan con `instantiate` (`default_parameters()`):

```python
{"segmentation": {"min_duration_off": 0.0},             # rellena silencios cortos dentro de un turno
 "clustering": {"threshold": 0.6, "Fa": 0.07, "Fb": 0.8}}
```

* `threshold` es el umbral del clustering aglomerativo que inicializa VBx. En VBx, `Fa` escala las estadísticas acústicas y `Fb` regulariza cuántos hablantes se crean: un `Fb` más alto tiende a dar **menos** hablantes (descripción general de VBx, **no verificado** para community-1).
* `min_duration_off` en `Uniform(0.0, 1.0)`: un valor como 0.3 s une turnos del mismo hablante separados por pausas cortas, lo que da subtítulos menos fragmentados.
* Cómo cambiarlos: `pipeline.instantiate({...})` con el dict completo, o leer los actuales con `pipeline.parameters(instantiated=True)` (API de `pyannote.pipeline`, **no verificado** en 4.x). Si el pipeline no está instanciado al llamarlo, se instancia solo con `default_parameters()` y avisa (leída, `__call__`).
* Ajustarlos automáticamente sobre datos propios: la CLI de 4.x trae `optimize` y `benchmark` (leída, CHANGELOG). Requiere referencias anotadas en formato `pyannote.database`.

## 8. Embeddings de hablante (leída)

`output.speaker_embeddings[s]` es el embedding del hablante `output.speaker_diarization.labels()[s]`. Un tercero lo describe como el centroide ponderado por VBx (snippet). Sirven para:

* **Reconocer al mismo hablante en varios archivos**, por ejemplo a la conductora de todos los episodios: similitud coseno contra un embedding guardado. El umbral se calibra con audio propio (**no verificado**).
* **Unir trozos** si un audio muy largo se diariza por partes ([05](05-rendimiento-y-vram.md) §5).

Para comparar contra una grabación de referencia fuera del pipeline, `pyannote/wespeaker-voxceleb-resnet34-LM` con `Inference(model, window="whole")` da un embedding por archivo (snippet). Desde 4.0, `Inference` solo acepta modelos ya instanciados (leída, CHANGELOG).

## 9. Inferencia por lotes (leída, 4.0.7)

`pipeline([archivo1, archivo2])` procesa en secuencia y devuelve un **iterador** de pares `(archivo, predicción)`. Las URI deben ser distintas. Con un solo archivo, devuelve el resultado directo.

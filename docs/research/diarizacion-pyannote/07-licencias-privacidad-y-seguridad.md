# 07. Licencias, privacidad y seguridad

## 1. Licencias

| Pieza | Licencia | Fuente |
| :--- | :--- | :--- |
| `pyannote.audio` (código) | MIT, © 2020 CNRS | [LICENSE](https://github.com/pyannote/pyannote-audio/blob/develop/LICENSE) (leída por el agente) |
| `speaker-diarization-community-1` (pipeline y pesos) | **CC-BY-4.0**: «released under the CC-BY-4.0 license and will always remain freely accessible» | [Tarjeta](https://huggingface.co/pyannote/speaker-diarization-community-1) (leída por el agente) |
| `segmentation-3.0` (repositorio aparte) | MIT | [Tarjeta](https://huggingface.co/pyannote/segmentation-3.0) (leída por el agente) |
| WhisperX (si se copia `assign_word_speakers`) | BSD-2-Clause, © 2024 Max Bain | [LICENSE](https://github.com/m-bain/whisperX/blob/main/LICENSE) (leída) |
| torch, torchcodec | BSD-3-Clause | LICENSE de cada uno (leída por el agente) |
| FFmpeg (si se empaqueta) | LGPL 2.1+, o GPL si se compila con `--enable-gpl` | [ffmpeg.org/legal](https://ffmpeg.org/legal.html) (leída por el agente) |

* CC-BY-4.0 permite copiar, redistribuir y adaptar con cualquier fin, **también comercial**, con atribución e indicando si hubo cambios ([deed](https://creativecommons.org/licenses/by/4.0/)).
* Las licencias por componente interno (segmentación, embedding WeSpeaker y PLDA de VBx) no están separadas en la tarjeta: rige la del repositorio (**no verificado** archivo por archivo).
* **No copiar código** de noScribe (GPL-3.0) ni de VoiceStudio (AGPL-3.0). Las ideas sí se pueden reimplementar.
* La propuesta de [04](04-integracion-con-faster-whisper.md) §4 es una implementación propia. Si se copia código de WhisperX, se conserva su aviso BSD-2.

## 2. Acceso restringido (*gated*)

* Texto visible: «You need to agree to share your Hugging Face information to access this model» y «we may email you occasionally with important news about pyannote models» (leída por el agente). Las condiciones completas solo se ven con sesión iniciada: **hay que leerlas antes de publicar**.
* El autor puede revocar el acceso a un repositorio restringido en cualquier momento ([docs de Hugging Face](https://huggingface.co/docs/hub/models-gated)). Depender de la descarga en cada instalación es un riesgo.
* Existe un espejo de terceros sin restricción (`DanieClar/stillscript-speaker-diarization-community-1`). Su propio README pide preferir el original. **No usarlo**: su razón de ser es saltarse el acceso restringido.
* En pyannote 4.x, **incluso `speaker-diarization-3.1`** exige aceptar community-1, por su PLDA ([#2044](https://github.com/pyannote/pyannote-audio/issues/2044), leída).

**Opciones para la app:**

| Opción | Ventaja | Costo |
| :--- | :--- | :--- |
| **A. El usuario pega su token de Hugging Face** y la app descarga una vez (como WhisperX y VoiceStudio) | Respeta las condiciones del autor y no redistribuimos nada | Hace falta una cuenta y aceptar condiciones. VoiceStudio tuvo quejas por esto ([nota anterior](../voicestudio-narracion/herramientas/07-diarizacion.md) §6) |
| B. Publicar los pesos en un espejo propio o dentro del instalador | Sin cuenta ni token | Legal según CC-BY si las condiciones completas no lo prohíben. Exige atribución y una decisión registrada en `docs/process/WARNING/` |
| C. Plan B sin acceso restringido: sherpa-onnx con `segmentation-3.0` (MIT) | Sin token ni torch | Otro pipeline, sin VBx ni salida exclusiva, y sin DER publicado |

**Recomendación**: empezar con **A**, con la UI guiando los pasos y un mensaje claro si el token no tiene acceso: un 401 o 403 suele ser porque falta aceptar las condiciones. Evaluar B solo después de leer las condiciones completas.

## 3. Atribución (texto propuesto para «Acerca de» y `NOTICE`)

> Diarización de hablantes: modelo `pyannote/speaker-diarization-community-1` de pyannote / pyannoteAI, bajo licencia Creative Commons Atribución 4.0 Internacional (https://creativecommons.org/licenses/by/4.0/). Fuente: https://huggingface.co/pyannote/speaker-diarization-community-1. Sin cambios en los pesos. Biblioteca pyannote.audio: licencia MIT, © 2020 CNRS.

Citas académicas que pide la tarjeta: Plaquet y Bredin (INTERSPEECH 2023), Wang et al. (WeSpeaker, ICASSP 2023) y Landini et al. (VBx, Computer Speech & Language 2022).

## 4. Privacidad: telemetría activada por defecto (leída)

* [`telemetry/config.yaml`](https://github.com/pyannote/pyannote-audio/blob/develop/src/pyannote/audio/telemetry/config.yaml): `metrics_enabled: true` y `otlp_endpoint: https://otel.pyannote.ai/v1/traces`.
* Qué envía (README, leída):
  * el origen del pipeline (el nombre oficial, `huggingface` o `local`) y su clase;
  * por cada archivo, **la duración** y los valores de `num_speakers`, `min_speakers` y `max_speakers`.

  Dicen que no envía nada que identifique al usuario.
* Esta app es local y promete no enviar datos. **Hay que apagarla siempre**, en el entorno del proceso y antes de importar:

```python
os.environ['PYANNOTE_METRICS_ENABLED'] = '0'   # o en el env del subproceso del motor
```

  También existe `from pyannote.audio.telemetry import set_telemetry_metrics; set_telemetry_metrics(False)` (leída, README).
* Un test del motor debe comprobar que la variable está en el entorno del subproceso.

## 5. Seguridad: ejecución de código desde `config.yaml` ([#2000](https://github.com/pyannote/pyannote-audio/issues/2000), abierto, leída)

* `Pipeline.from_pretrained` resuelve nombres de clases y funciones escritos en el `config.yaml` del repositorio (`pipeline.name` y `preprocessors.*.name`) y los llama con parámetros del mismo archivo. Un repositorio malicioso puede ejecutar `os.system` al cargar.
* Los pipelines oficiales solo usan clases de `pyannote.*` (comentario en el issue). Hay una propuesta de lista permitida con `trust_remote_code`, todavía sin fusionar.
* **Mitigación**: cargar solo community-1, con la revisión **fijada** en la receta, desde la carpeta local descargada por la app. Nunca aceptar un nombre de repositorio que escriba el usuario.

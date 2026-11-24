# 01. Panorama y elección

> Por qué pyannote 4.x con community-1 y no otra herramienta. Primera ronda de investigación (2026-11-24).

## 1. Qué se necesita

* faster-whisper 1.2.1 ya entrega segmentos con palabras y sus tiempos: `words_payload` en [transcribe_main.py](../../../server/src/content_studio/transcription/transcribe_main.py) usa `word_timestamps=True` y `vad_filter=True`.
* Falta saber **quién dice cada palabra**. El diarizador corre aparte y su salida se cruza con las palabras.
* Restricciones: es local, en Windows, con 8 GB de VRAM y un modelo a la vez en la GPU ([turno-gpu](../../../.agents/rules/turno-gpu.md)). Necesita licencia comercial y un venv por motor.

## 2. Pipelines que ya juntan Whisper y diarización

| Herramienta | Licencia | Qué hace | Veredicto |
| :--- | :--- | :--- | :--- |
| [WhisperX](https://github.com/m-bain/whisperX) v3.8.6 (2026-05-25), 3.8.7rc1 (2026-06-26) | BSD-2-Clause (leída) | faster-whisper, alineación wav2vec2 y pyannote. Su diarizador por defecto es community-1 (leída, `diarize.py`) | **Referencia de código**, no dependencia: fija `torch~=2.8.0` y `torchcodec>=0.6,<0.8` (leída, `pyproject.toml`), y traería su propio faster-whisper |
| [whisper-diarization](https://github.com/MahmoudAshraf97/whisper-diarization) | BSD-2-Clause (snippet) | faster-whisper, ctc-forced-aligner, TitaNet de NeMo y realineado por puntuación | Solo como idea de realinear por puntuación. Depende de NeMo y su modo paralelo pide ≥ 10 GB (snippet) |
| [noScribe](https://github.com/kaixxx/noScribe) | GPL-3.0 (leída) | App con faster-whisper y pyannote | No se puede copiar código a un producto que no sea GPL |
| [insanely-fast-whisper](https://github.com/vaibhavs10/insanely-fast-whisper) | Apache-2.0 (snippet) | Transformers, flash-attn y pyannote | No usa faster-whisper |
| [stable-ts](https://github.com/jianfch/stable-ts) | MIT | Timestamps refinados | Archivado y sin diarización |

## 3. Diarizadores independientes

| Motor | Licencia (código / pesos) | Veredicto |
| :--- | :--- | :--- |
| **pyannote 4.x + community-1** | MIT / CC-BY-4.0 (leída) | **Elegido**. DER menor que 3.1 en 10 de 12 benchmarks, salida exclusiva para transcripción y `num_speakers`/`min_speakers`/`max_speakers` |
| pyannote 3.1 (`speaker-diarization-3.1`) | MIT / MIT | Peor DER y sin salida exclusiva. En pyannote 4.x igual exige aceptar community-1 por el PLDA ([#2044](https://github.com/pyannote/pyannote-audio/issues/2044), leída). Los mantenedores recomiendan usar los pipelines viejos con versiones viejas |
| NVIDIA Sortformer v2.1 (streaming, 4 hablantes) | NVIDIA Open Model License (snippet) | Máximo 4 hablantes y NeMo pesado, sin soporte documentado en Windows |
| DiariZen (BUT) | MIT / **CC-BY-NC-4.0** (snippet) | Pesos no comerciales |
| sherpa-onnx (segmentación 3.0 de pyannote en ONNX y embeddings 3D-Speaker) | Apache-2.0 / según cada archivo | Alternativa **sin torch** para CPU y sin acceso restringido. No tiene DER publicado y no tiene VBx |
| 3D-Speaker, SpeechBrain ECAPA, Resemblyzer, simple-diarizer | varias | Son embeddings sueltos o envoltorios: habría que armar el pipeline completo |
| Picovoice Falcon | Propietaria, con clave en línea | No es local de verdad |
| VibeVoice-ASR (9B), DiarizationLM (8B) | MIT / investigación | No caben en 8 GB. DiarizationLM solo cubre inglés |

## 4. Por qué community-1

1. **Calidad**: el CHANGELOG 4.0.0 explica que usa clustering VBx en lugar del aglomerativo de 3.1, lo que mejora el conteo y la asignación de hablantes (leída). Tabla de DER en [06](06-calidad-y-evaluacion.md).
2. **Hecho para transcripciones**: la salida exclusiva viene del modelo comercial `precision-2` y «simplifica la reconciliación entre los tiempos finos de la diarización y los tiempos (a veces imprecisos) de la transcripción» (leída, CHANGELOG 4.0.0).
3. **Uso offline oficial**: el pipeline y sus modelos internos viven en un solo repositorio. Se clona una vez y se carga desde una carpeta (leída, CHANGELOG 4.0.0).
4. **Licencia comercial** con atribución ([07](07-licencias-privacidad-y-seguridad.md)).
5. **Mantenimiento activo**: 10 versiones entre 2025-09-29 y 2026-11-19. La última, 4.1.1, salió hace 5 días (leída, PyPI).

**Plan B** si el acceso restringido o torch resultan inviables: sherpa-onnx con `segmentation-3.0` (MIT) en ONNX, sin token y en CPU. Se mide antes con [06](06-calidad-y-evaluacion.md) §4.

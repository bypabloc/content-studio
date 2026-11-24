# Spec 035: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `035-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-035/` o `tmp/spec-035/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git log origin/dev --merges --oneline | grep -q 'feature/034-diarization-engine' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/engines/recipes/pyannote.json || echo FALLA
```

## 2. Contexto

La 034 deja instalable el motor, pero ningún trabajo lo usa. La transcripción entrega palabras con tiempos (`words_payload`) y nadie sabe de quién es cada una. Las secciones de la 036 a la 038 necesitan tres cosas:

* un trabajo que diarice un archivo;
* otro que transcriba con hablantes;
* los archivos de salida: turnos, exportaciones y audio por hablante.

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Turno | Tramo `{start, end, speaker}` de un hablante | `turns.json` |
| Diarización exclusiva | Turnos sin solapes: un hablante por instante | `exclusive_diarization` |
| Bloque | Palabras seguidas del mismo hablante | `blocks.blocks()` |
| RTTM | Formato estándar de turnos (`SPEAKER <uri> 1 <inicio> <duración> <NA> <NA> <hablante> <NA> <NA>`) | `exports.rttm()` |

### Hallazgos de la exploración

- **Formato de la transcripción**:
  * `transcription/transcribe_main.py` (`words_payload`) entrega `{language, language_probability, duration, text, segments: [{start, end, text, words: [{start, end, word, probability}]}]}`;
  * ya extrae el audio a `<out>/audio-16k.wav`;
  * se relanza en `.venv-whisper` con `common.process.use_venv`.
- **El servicio `transcribe`** (`services/transcribe.py`) tiene `RESOURCE='gpu'` y escribe `words.json`. La cola toma el candado una vez por trabajo (`jobs/worker.py:_run_gpu`).
- **Formato del progreso**: `common/progress.py` emite `@@progress {"p", "stage"}` y `jobs/runner.py` lo interpreta.
- **La caché de transcripción** (`transcription/cache.py` y la tabla `transcripts`) usa como clave ruta, mtime, tamaño, modelo e idioma. Es el patrón que sigue `diarizations`.
- **La verificación de motores** (`engines/verification.py:verify_engine`) devuelve `Unsupported engine family` para lo que no sea narración, música o asistente.
- **La API de pyannote 4.1.1** (leída el 2026-11-24, [investigación 03](../../../research/diarizacion-pyannote/03-api-y-uso.md)):
  * `DiarizeOutput.serialize()` entrega `diarization` y `exclusive_diarization`;
  * `speaker_embeddings` sigue el orden de `labels()`;
  * el `hook` informa las etapas `segmentation` y `embeddings` con `completed` y `total`.
- **Riesgos medidos por terceros** ([investigación 05](../../../research/diarizacion-pyannote/05-rendimiento-y-vram.md)):
  * con lotes de 32, el pico de VRAM llega a unos 10 GB; con 4 baja a 0,46 GiB;
  * leer desde archivo es hasta 21× más lento que pasar el audio en memoria;
  * pyannote apaga TF32 en todo el proceso;
  * con archivos de unos 5 s falla si no se precarga el audio.
- **Telemetría**: `telemetry/config.yaml` trae `metrics_enabled: true` ([investigación 07](../../../research/diarizacion-pyannote/07-licencias-privacidad-y-seguridad.md)).

## 3. Solución

* Un paquete nuevo `server/src/content_studio/diarization/`:
  * en stdlib: unión, bloques, exportaciones, caché, `speakers.json` y comandos de ffmpeg;
  * `diarize_main.py`, que se relanza en `.venv-diarize`;
  * `transcribe_speakers_main.py`, que orquesta transcripción y diarización.
* Dos servicios, `diarize` (GPU) y `diarize.split` (CPU), más un parámetro `diarize` en `transcribe`.
* `studio diarize` y la rama `diarization` de la verificación de motores.

Decisiones:

- **D-1: unión con la exclusiva y vecino a 1 s o menos** — es la salida que pyannote recomienda para casar con transcripciones. Se descarta copiar `assign_word_speakers` de WhisperX tal cual: usa la diarización con solapes y el punto medio, y deja palabras sin hablante por defecto ([investigación 04](../../../research/diarizacion-pyannote/04-integracion-con-faster-whisper.md)).
- **D-2: proceso propio, audio en memoria y lote de 4** — evita el pico de VRAM, la lectura lenta y el TF32 global. Se descarta pasar la ruta del archivo, porque depende de las DLL de FFmpeg que necesita torchcodec en Windows.
- **D-3: un orquestador en la Python del server** — los dos modelos viven en venvs distintos y deben correr en secuencia. Se descarta llamar a pyannote desde `transcribe_main`, que corre en `.venv-whisper`. También se descarta encadenar dos trabajos en el worker: soltaría el candado entre los dos y complica el progreso.
- **D-4: tabla `diarizations`** — así el Limpiador y Subtítulos (038) diarizan una sola vez por archivo. Se descarta meter los turnos en la caché de transcripción, que cambiaría su clave y su formato.
- **D-5: `diarize.split` bajo demanda, con silencio** — un audio de 1 h y 4 hablantes son 4 archivos de 1 h, que no deben crearse sin pedirlos. Con silencio se mantiene la sincronía para el Editor. Se descarta unir solo los tramos, porque pierde la sincronía; queda en «Fuera de alcance».
- **D-6: `speakers.json` aparte** — renombrar no reescribe turnos ni palabras. Se descarta guardar nombres en la base, porque son datos del trabajo, como `params.json`.
- **D-7: atajos sin modelo** — los embeddings fallan con menos de unos 2 s (pyannote #1961) y con un solo hablante no hay nada que decidir.
- **D-8: `studio diarize`** — es una línea en el parser y permite verificar sin la UI.

## 4. Fuera de alcance

- La UI: las secciones Transcripción (036) y Hablantes (037), y la integración en Subtítulos, el Editor y el Limpiador (038).
- Audio por hablante con solo sus tramos unidos, sin silencio.
- Reconocer al mismo hablante entre archivos con `speaker_embeddings` (se guardan, pero no se usan).
- Diarizar audios de varias horas por trozos ([investigación 05](../../../research/diarizacion-pyannote/05-rendimiento-y-vram.md) §5).
- Ajustar los hiperparámetros (`threshold`, `Fa`, `Fb`, `min_duration_off`) desde la UI.
- Alineación forzada con wav2vec2.

## 5. Criterios de aceptación

- **AC-1**: Given palabras y turnos exclusivos When se llama a `assign_speakers(words, turns)` Then:
  * cada palabra que se solapa con un turno toma el hablante con más solape;
  * una palabra en un hueco toma el turno más cercano si está a 1 s o menos;
  * una palabra a más de 1 s, o sin turnos, queda con `speaker: None`.
- **AC-2**: WHEN se agrupan palabras con hablante THEN cada cambio de hablante abre un bloque, y una palabra aislada de otro hablante entre dos del mismo, con menos de 0,3 s de pausa, se absorbe.
- **AC-3**: WHEN se exportan los turnos THEN:
  * `turns.rttm` tiene una línea por turno exclusivo, con inicio y duración de 3 decimales;
  * `turns.csv` tiene la cabecera `start,end,speaker,name`;
  * `turns.json` trae `duration, speakers, diarization, exclusive_diarization`.
- **AC-4**: WHEN `diarize_main` corre con el pipeline simulado THEN:
  * el entorno tiene `PYANNOTE_METRICS_ENABLED=0` y `HF_HUB_OFFLINE=1`;
  * `from_pretrained` recibe la carpeta local;
  * `embedding_batch_size` es 4;
  * la llamada recibe `{"waveform", "sample_rate": 16000}` y `num_speakers` o `min/max_speakers`;
  * emite `@@progress` creciente y escribe `turns.json` y `embeddings.json`.
- **AC-5**: WHEN corre `diarize.split` THEN se arma un comando de ffmpeg por hablante que escribe `speakers/<id>.wav`, con la duración y la frecuencia de muestreo del original y silencio fuera de sus turnos.
- **AC-6**: WHEN `verify_engine('pyannote')` corre THEN diariza un audio de prueba de 6 s, generado con ffmpeg, y se da por bueno si `turns.json` es válido. La verificación ya no responde `Unsupported engine family`.
- **AC-7**: WHEN se encola `diarize` THEN:
  * `validate` rechaza un archivo inexistente (`file_not_found`), un `num_speakers` fuera de 1 a 20 y `min > max` (`invalid_speakers`), y el motor sin instalar (`engine_not_installed`);
  * `RESOURCE` es `gpu`;
  * la carpeta del trabajo termina con `turns.json`, `turns.rttm`, `turns.csv` y `speakers.json`.
- **AC-8**: Given un archivo ya diarizado con los mismos parámetros When se vuelve a pedir Then se reusa `<datos>/diarizations/<sha1>.json` sin lanzar `diarize_main`. Lo mismo vale cuando el audio dura menos de 3 s o se pide `num_speakers=1` (D-7).
- **AC-9**: WHEN se encola `transcribe` con `diarize: true` THEN `words.json` trae `speaker` en cada palabra y en cada segmento (el dominante), junto a `speakers.json`. El progreso avanza en dos tramos: transcripción de 0 a 0,6 y diarización de 0,6 a 0,95.
- **AC-10**: WHEN se encola `transcribe` sin `diarize` THEN el comando y `words.json` son idénticos a los de hoy.
- **AC-11**: WHEN se corre `uv run studio diarize audio.wav --speakers 2` THEN encola el trabajo y muestra la carpeta de salida. `--speakers 0` o `--min-speakers 3 --max-speakers 2` salen con 2 y un mensaje en inglés. `--help` no pregunta nada.

## 6. Debe sonar / no debe sonar

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| `speakers/<id>.wav` de `diarize.split` | La misma duración que el original (±10 ms) y la voz de ese hablante en sus turnos | Voz de otro hablante fuera de un solape, clics en los bordes de cada turno, ni un cambio de volumen en la voz que queda |

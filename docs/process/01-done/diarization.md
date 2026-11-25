# Diarización: quién habla y cuándo

**Qué resuelve**: separa un audio por hablante. Dice cuándo habla cada uno (turnos), deja un WAV por hablante y, en una transcripción, marca el hablante de cada palabra y de cada segmento.

**Qué hace hoy**

- `studio diarize <archivo> [--speakers N | --min-speakers A --max-speakers B]`: encola la diarización y muestra la carpeta de salida.
- Trabajo `diarize`: turnos en `turns.json`, `turns.rttm` y `turns.csv`; nombres y colores en `speakers.json`; embeddings en `embeddings.json`.
- Trabajo `diarize.split`: un WAV por hablante en `speakers/<id>.wav`, con silencio fuera de sus turnos exclusivos. Recibe la carpeta de turnos de una diarización.
- Trabajo `transcribe` con `diarize: true`: `words.json` con `speaker` en cada palabra y segmento, junto a `speakers.json`.
- Un audio de menos de 3 s, o con `num_speakers=1`, es un solo hablante sin cargar el modelo. El mismo audio con los mismos hablantes reusa su resultado (`<datos>/diarizations/<sha1>.json`).
- Sección **Hablantes** (spec 037): identifica quién habla y cuándo sin transcribir. Muestra la línea de tiempo con los turnos, nombres editables (se guardan al instante), los archivos de turnos, un audio por hablante y «Abrir en el Editor» con un marcador por turno.

**Dónde vive**: `server/src/content_studio/diarization/`. pyannote corre en `.venv-diarize` (receta `pyannote`, modelo `pyannote/speaker-diarization-community-1` con acceso restringido), sin red y sin telemetría. Los servicios están en `services/diarize.py`, `diarize_split.py` y `transcribe.py`.

**Historial**

- Spec 034: motor pyannote y credencial de Hugging Face (PR #115).
- Spec 035: unión palabra-hablante, trabajos, caché, CLI y transcripción con hablantes.
- Spec 037: sección Hablantes (identificar quién habla y cuándo): línea de tiempo, nombres, archivos de turnos, un audio por hablante y «Abrir en el Editor».

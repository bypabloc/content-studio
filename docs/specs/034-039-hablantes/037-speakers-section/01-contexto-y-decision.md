# Spec 037: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `037-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-037/` o `tmp/spec-037/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git log origin/dev --merges --oneline | grep -q 'feature/036-transcription-section' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/api/routes/speakers.py || echo FALLA
```

## 2. Contexto

El usuario quiere una herramienta aparte para **solo diarizar**: saber quién habla y cuándo sin esperar la transcripción. Le sirve para:

* separar las voces de una entrevista;
* preparar la edición;
* sacar un audio por persona.

La 035 dejó los trabajos `diarize` y `diarize.split`, y la 036 los componentes de hablantes.

### Hallazgos de la exploración

- **Onda con regiones**: `client/src/features/cleaner/ReviewWave.tsx` dibuja WaveSurfer con regiones arrastrables. Su `start` y su `end` se miden con la duración del archivo ([WARNING 013-regiones-duracion-del-analisis](../../../process/WARNING/013-regiones-duracion-del-analisis.md)).
- **Picos del audio**: los sirve `/media/peaks` (la Biblioteca los usa).
- **Marcadores del Editor**: el proyecto del Editor tiene `markers` (`server/src/content_studio/editor/store.py` los crea vacíos, y `ops.py` los agrega y edita). Un proyecto vive en `out/editor/<fecha>-<slug>/project.json`.
- **Abrir en Editor** ya existe desde otras secciones (`client/src/shared/navigation/`).
- **Abrir carpeta**: hay un patrón con el *opener* de Tauri ([WARNING 005-opener-abrir-carpeta](../../../process/WARNING/005-opener-abrir-carpeta.md)).

## 3. Solución

* API: `GET /diarizations/{job_id}` con los turnos, los hablantes, las rutas de los archivos y los WAV por hablante si existen. `POST /editor/projects/from-diarization`.
* Sección `speakers` con:
  * el formulario: archivo y número de hablantes;
  * la línea de tiempo con regiones por turno;
  * `UISpeakerLegend`;
  * archivos de turnos;
  * «Un audio por hablante» (encola `diarize.split` y muestra un reproductor por hablante);
  * «Abrir en el Editor».

Decisiones:

- **D-1: sección propia** — la pidió el usuario: un módulo aparte para solo diarizar. Se llama «Hablantes» porque «Diarizar» es una palabra técnica.
- **D-2: regiones de solo lectura** — corregir turnos queda fuera de alcance. Se descarta reusar `ReviewWave` tal cual, porque sus regiones son de cortes arrastrables. Se extrae un organismo de onda con regiones configurables solo si el código lo pide (tercer uso).
- **D-3: marcadores** — el Editor ya los soporta. Se descarta un clip por turno, que fragmentaría el audio. El mínimo de 0,5 s evita un marcador por cada «ajá».
- **D-4: archivos en su carpeta** — ya están ahí. Se descarta «Guardar como», porque sería un diálogo y una copia más.
- **D-5: navegar por turnos** — es útil para revisar sin generar audio.

## 4. Fuera de alcance

- Corregir turnos a mano: mover bordes, partir, unir o reasignar.
- Unir dos hablantes.
- Reconocer a la misma persona en otros archivos.
- Audio por hablante con solo sus tramos unidos (sin silencio).
- Transcribir desde esta sección: para eso está Transcripción.

## 5. Criterios de aceptación

- **AC-1**: WHEN el usuario abre «Hablantes», elige un archivo, el modo «Automático» y pulsa «Identificar» THEN se encola `diarize` con `{input}` (más `num_speakers` o el rango si los pidió), y la sección muestra el progreso.
- **AC-2**: WHEN termina THEN la onda muestra:
  * una región por turno exclusivo, con el color y el nombre de su hablante;
  * debajo, la leyenda con la duración total de cada hablante.

  Al hacer clic en una región, se reproduce desde su inicio. Con «Solo este hablante», las demás regiones se atenúan y ← y → saltan entre sus turnos.
- **AC-3**: WHEN el usuario renombra o cambia el color de un hablante THEN las etiquetas y colores de las regiones cambian al instante y se guardan (`PUT /jobs/{id}/speakers`). `turns.csv` lleva el nombre nuevo.
- **AC-4**: WHEN la sección carga un resultado THEN `GET /diarizations/{id}` entrega `turns.json`, `turns.rttm` y `turns.csv` con sus rutas, y la sección los lista con «Abrir carpeta». Un trabajo que no es `diarize` responde 409 `not_a_diarization`.
- **AC-5**: WHEN el usuario pulsa «Un audio por hablante» THEN se encola `diarize.split`. Al terminar, aparece un reproductor por hablante con su nombre, y los WAV duran lo mismo que el original.
- **AC-6**: WHEN el usuario pulsa «Abrir en el Editor» THEN se crea un proyecto con el archivo como clip en la pista 1 y un marcador por turno exclusivo de 0,5 s o más, con el nombre del hablante y sus tiempos, y la app abre el Editor con ese proyecto.
- **AC-7**: WHEN se abre `#/speakers?from_job=<id>` desde la cola o la Biblioteca THEN se muestra ese resultado sin volver a diarizar.

## 6. Debe sonar / no debe sonar

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| `speakers/<id>.wav` desde la sección | Lo de la [035 §6](../035-diarize-job/01-contexto-y-decision.md#6-debe-sonar--no-debe-sonar) | Lo de la 035 §6 |

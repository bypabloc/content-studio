# Spec 036: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `036-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-036/` o `tmp/spec-036/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git log origin/dev --merges --oneline | grep -q 'feature/035-diarize-job' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/diarization/transcribe_speakers_main.py || echo FALLA
```

## 2. Contexto

Hoy no hay dónde transcribir un archivo y leer el texto: la transcripción solo existe dentro de Subtítulos, el Limpiador, Mezcla y el panel de subtítulos del Editor. La 035 deja el trabajo `transcribe` con hablantes, pero nada lo muestra.

### Hallazgos de la exploración

- **No existe la sección.** `client/src/app/nav.ts` tiene en «Editar» a cleaner, subtitles, convert, normalize, mix, editor y library. `Shell.tsx` carga cada sección de forma perezosa según su `id`.
- **El modelo y el idioma solo se eligen en el Limpiador.** `UIWhisperModelSelect` (`shared/components/molecules/UIWhisperModelSelect/`) recuerda `select.whisper.model`. Subtítulos no manda `model` ni `language` (`SubtitlesPage.tsx:63`).
- **Patrón de encolado**:
  * `POST /jobs` con `kind` y `params`;
  * el progreso llega por SSE a `['jobs', id]` (`shared/api/events.ts`);
  * `SubtitleTracksPanel.tsx` muestra `UIProgress` mientras espera.
- **Ya hay un patrón de palabras clicables sincronizadas con el reproductor**: `CleanReview.tsx`, con `shared/media/useSyncedMedia.ts`.
- **Crear subtítulos desde un `words.json`** ya existe: `POST /subtitles/from-transcript` (`api/routes/subtitles.py`).
- **Abrir un resultado anterior**: la Biblioteca y la cola lo hacen con `?from_job=` (`shared/hooks/useFromJob.ts`).

## 3. Solución

* API: `GET /jobs/{id}/transcript`, `GET/PUT /jobs/{id}/speakers` y `POST /jobs/{id}/transcript/export`.
* Sección `transcription` con un formulario y un resultado:
  * formulario: archivo, modelo, idioma, «Identificar hablantes» y número de hablantes;
  * resultado: reproductor, texto por bloques, leyenda editable, exportar TXT y «Crear subtítulos».

Decisiones:

- **D-1: sección propia** — la eligió el usuario.
- **D-2: `speakers.json` con dos rutas** — un solo lugar para Transcripción y Hablantes. Se descarta guardar nombres en la base: son datos del trabajo.
- **D-3: formato del TXT** — se lee como un acta. Se descarta DOCX, porque sería una dependencia nueva.
- **D-4: componentes compartidos** — tienen tres usos (036, 037 y 038), así que la abstracción se justifica (plan-format §0).
- **D-5: `from_job` en vez de un historial** — ya existe. Se descarta una lista propia, que duplicaría la cola.

## 4. Fuera de alcance

- Editar el texto de la transcripción (para eso está Subtítulos).
- Exportar DOCX o PDF.
- Unir dos hablantes en uno o partir un bloque a mano (queda para Hablantes o Subtítulos en otra spec).
- Mostrar el hablante en Subtítulos, el Editor o el Limpiador: es la 038.
- Un subcomando `studio transcribe`.

## 5. Criterios de aceptación

- **AC-1**: WHEN se abre la app THEN «Transcripción» aparece en «Editar» con su ícono, y la paleta Ctrl+K la encuentra.
- **AC-2**: WHEN el usuario elige un archivo, el modelo, el idioma y activa «Identificar hablantes» con «Exacto: 2» THEN se encola `transcribe` con `{input, model, language, diarize: true, num_speakers: 2}` y la sección muestra el progreso. El modelo y el idioma se recuerdan.
- **AC-3**: Given `pyannote` no instalado When se abre la sección Then «Identificar hablantes» está deshabilitado, con el texto «Instala el motor de diarización» y un enlace a Motores.
- **AC-4**: WHEN termina un trabajo con hablantes THEN el resultado muestra bloques con el nombre y el color de cada hablante. Al hacer clic en una palabra, el reproductor salta a ese tiempo, y la palabra que suena se resalta. Sin hablantes, muestra párrafos por segmento.
- **AC-5**: WHEN el usuario renombra «Hablante 1» como «Ana» o cambia su color THEN:
  * `PUT /jobs/{id}/speakers` lo guarda y el texto se actualiza;
  * al reabrir con `?from_job=`, sigue así;
  * un nombre vacío o de más de 40 caracteres, o un color que no es `#rrggbb`, responde 422.
- **AC-6**: WHEN el usuario exporta el texto THEN la carpeta del trabajo tiene `transcript.txt` con un bloque por turno, `[hh:mm:ss] Ana: …`, y los nombres actuales. Sin marcas de tiempo, solo `Ana: …`. «Abrir carpeta» muestra el archivo.
- **AC-7**: WHEN el usuario pulsa «Crear subtítulos» THEN se crea un proyecto con `/subtitles/from-transcript` y la app navega a Subtítulos con ese proyecto abierto.

## 6. Debe sonar / no debe sonar

No aplica.

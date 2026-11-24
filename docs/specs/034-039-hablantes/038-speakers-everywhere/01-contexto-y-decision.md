# Spec 038: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `038-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-038/` o `tmp/spec-038/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

```bash
git log origin/dev --merges --oneline | grep -q 'feature/037-speakers-section' || echo FALLA
git cat-file -e origin/dev:server/src/content_studio/diarization/run.py || echo FALLA
```

## 2. Contexto

La 013 y la 014 dejaron fuera, a propósito, la diarización y los colores por hablante:

* `docs/specs/001-017-studio/013-whisper-cleaner/01-contexto-y-decision.md`: «Diarización (quién habla)»;
* `014-subtitles/01-contexto-y-decision.md`: «Diarización y colores por hablante».

Con la 035 a la 037 ya existe el motor, los trabajos y los componentes. Falta llevar el hablante a las secciones que ya transcriben.

### Hallazgos de la exploración

- **Segmentación**: `subtitles/segment.py` corta en puntuación fuerte, luego débil, a 42 caracteres, 2 renglones y 7 s. No sabe de hablantes.
- **Documento**: `subtitles/document.py` arma `{version: 1, source, language, cues: [{id, start, end, text, words}], style, tracks}`. `split`, `merge`, `shift` y `set_text` son funciones puras.
- **Orígenes**:
  * `subtitles/create_main.py` transcribe con caché para los orígenes `file` y `narration`;
  * para `cleaner`, mueve las palabras con `clean_words` y `remap` según `cuts.json`;
  * `api/routes/subtitles.py` (`from-transcript`) crea el documento desde un `words.json`.
- **ASS** (`subtitles/ass.py`): tiene `_classic`, `_social` y `_karaoke`. El client tiene su propio `ass.ts` para la vista previa con JASSUB.
- **Exportar SRT y VTT**: `subtitles/formats.py` (`export.render`).
- **Client de Subtítulos**:
  * `CueEdit` y `WordEdit` (`features/subtitles/cues.ts`) no tienen hablante;
  * `CueList.tsx` muestra el número y las palabras;
  * `SubtitlesPage.tsx` encola `subtitles.create` con `{origin, input}`.
- **Editor**:
  * la pista de subtítulos solo apunta a un proyecto (`editor/model/types.d.ts`) y no tiene clips, así que su carril en `Timeline.tsx` queda vacío;
  * `SubtitleTracksPanel.tsx` transcribe la mezcla con `large-v3-turbo` y `auto` fijos.
- **Limpiador**:
  * `clean/analyze_main.py` transcribe con caché y escribe `cuts.json` con la ruta del transcript;
  * `CleanReview.tsx` muestra las palabras como botones;
  * `CleanerPage.tsx` elige modelo e idioma.

## 3. Solución

* **Server de Subtítulos**:
  * la segmentación respeta al hablante;
  * el documento y sus operaciones llevan `speaker`;
  * `create_main` y `from-transcript` propagan los hablantes, y `create_main` acepta `diarize`;
  * ASS por hablante y prefijo al exportar.
* **Client de Subtítulos**:
  * el interruptor y el número de hablantes en «Nuevo proyecto», que ahora manda también `model` y `language`;
  * un chip de hablante por cue, editable;
  * `UISpeakerLegend` en el editor;
  * la casilla «Incluir nombres» al exportar.
* **Editor**: el interruptor en «Transcribir la mezcla» y un carril que dibuja los cues por color.
* **Limpiador**: el interruptor en el análisis, las palabras coloreadas y la leyenda en la revisión.

Decisiones:

- **D-1: campos opcionales** — no rompe los documentos existentes. Se descarta subir la versión, que exigiría una migración de los proyectos.
- **D-2: cortar por hablante** — un subtítulo con dos voces confunde. Se descarta cortar solo cuando hay puntuación.
- **D-3: color en `classic` y `social`** — es lo que pidió el usuario («etiqueta y color»). Se descarta el karaoke, que ya usa el color para el avance.
- **D-4: prefijo opcional** — muchas plataformas muestran el texto tal cual. Se descarta que venga encendido.
- **D-5: el Limpiador diariza con caché** — así «Subtitular» desde el Limpiador no repite la diarización. Se descarta diarizar el archivo ya limpio, que daría otra numeración de hablantes.
- **D-6: bloques de solo lectura** — es lo que pidió el usuario. Se descarta editar cues desde la línea de tiempo, que queda fuera de alcance.

## 4. Fuera de alcance

- Editar o mover cues desde la línea de tiempo del Editor.
- Un estilo ASS distinto por hablante (fuente o posición): solo cambia el color.
- Hablantes en Mezcla (ducking) y en la narración.
- Traducir conservando hablantes más allá de copiar `speaker` al cue traducido, que sí se hace si el cue mantiene su `id`.

## 5. Criterios de aceptación

- **AC-1**: Given palabras con dos hablantes que alternan dentro de una frase When se segmenta Then ningún cue tiene palabras de dos hablantes, y cada cue lleva `speaker`. Sin hablantes, los cues son idénticos a los de hoy (caracterización).
- **AC-2**: WHEN se crea un proyecto con `origin: file` y `diarize: true` (o desde una transcripción con hablantes, o desde el Limpiador con hablantes) THEN el documento trae `speakers` con nombres y colores, y `speaker` en cada cue. `split` y `merge` conservan el hablante; `merge` de dos hablantes distintos toma el del primero.
- **AC-3**: WHEN se genera el ASS de un documento con hablantes en `classic` o `social` THEN cada evento lleva `{\1c&HBBGGRR&}` con el color de su hablante, el mismo en el server (quemado) y en el client (vista previa). En `karaoke` no cambia.
- **AC-4**: WHEN se exporta con `speaker_labels: true` THEN el SRT empieza cada cue con `Ana: ` y el VTT con `<v Ana>`. Con `false`, la salida es la de hoy.
- **AC-5**: WHEN el usuario abre un proyecto con hablantes THEN:
  * cada cue muestra un chip con el nombre y el color de su hablante;
  * el chip permite cambiar el hablante de ese cue;
  * la leyenda permite renombrar y cambiar colores, y la vista previa se actualiza;
  * todo se guarda con el guardado automático.
- **AC-6**: WHEN el usuario crea un proyecto desde un archivo con «Identificar hablantes» THEN se encola `subtitles.create` con `{origin: file, input, model, language, diarize: true, …speakers}`. Sin el motor instalado, el interruptor está deshabilitado con su enlace.
- **AC-7**: WHEN en el Editor se transcribe la mezcla con «Identificar hablantes» THEN el trabajo `transcribe` lleva `diarize: true`, y el carril de la pista de subtítulos dibuja un bloque por cue con el color y el nombre de su hablante, alineado con la regla de tiempo.
- **AC-8**: WHEN se analiza en el Limpiador con «Identificar hablantes» THEN:
  * `cuts.json` apunta también a los turnos;
  * la revisión colorea cada palabra con su hablante y muestra la leyenda;
  * «Subtitular» crea un proyecto con los hablantes ubicados en el tiempo del archivo limpio.

## 6. Debe sonar / no debe sonar

No aplica: el audio no cambia. El quemado se verifica por imagen (03).

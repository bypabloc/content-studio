# 038: decisiones de los hablantes en subtítulos (fase 1, server)

- **Contexto**: los cues de `segment` mezclan hablantes si la frase sigue, y el documento de subtítulos no sabe de hablantes. Hacía falta sin romper los proyectos que ya existen (AC-1).
- **Elegida**: la segmentación corta primero en cada cambio de hablante (`_runs`) y luego sigue igual. Sin hablantes hay un solo trozo y el resultado es el de siempre. El documento suma `speaker` en cada cue y `speakers` ({id: {name, color}}) sin subir `version`: son campos opcionales (D-1 y D-2 de la spec).
- **Descartadas**: cortar solo donde hay puntuación (un cue con dos voces confunde, D-2); subir la versión del documento (migración de todos los proyectos).
- **Cómo revertir**: volver a `segment` sin `_runs`; quitar `speaker` de `_cue`, `_cue_from_words` y `_document`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/subtitles/test_segment.py` (`test_ac1_corta_en_cambio_de_hablante` y la caracterización sin hablantes).

- **Contexto**: la spec pide `server/tests/integration/test_characterization.py::test_ac1_sin_hablantes_igual`. Ningún fixture generado cambia con esta fase: la forma del cue sin hablantes está fijada en la prueba unitaria.
- **Elegida**: `test_ac1_sin_hablantes_el_cue_tiene_la_forma_de_siempre` en `test_segment.py` (unitaria), sin tocar `fixtures/`.
- **Descartada**: regenerar fixtures (cambiarían la salida sin motivo).

- **Contexto**: `set_speaker` cambia el hablante de un cue, y `merge` toma el de sus palabras; sin cambiar las palabras, una unión posterior volvería al hablante viejo.
- **Elegida**: `set_speaker` cambia el cue y el hablante de sus palabras. `merge` conserva el del primero (AC-2).
- **Descartada**: guardar el hablante solo en el cue (se pierde al unir).

- **Contexto**: el ASS debe pintar cada evento con el color de su hablante (AC-3), y `karaoke` ya usa el color para el avance.
- **Elegida**: `\1c` con el color del hablante en cada evento de `classic` y `social`; en `social` el relleno de las demás palabras también es el del hablante, y la palabra resaltada conserva el color de resaltado. `karaoke` no cambia (D-3).
- **Descartadas**: `\c` dentro de cada palabra (más etiquetas, mismo efecto); cambiar la fuente o la posición por hablante (fuera de alcance).
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/subtitles/test_ass.py`.

- **Contexto**: SRT y VTT deben poder llevar el nombre del hablante (AC-4).
- **Elegida**: `speaker_labels` (por defecto `false`): en SRT «Ana: » delante del texto; en VTT `<v Ana>`. Sin la opción, la salida es la de hoy (D-4).
- **Cómo comprobarla**: `test_ac4_el_nombre_del_hablante_va_en_srt_y_vtt_solo_si_se_pide` y `test_ac4_exportar_con_speaker_labels_pone_el_nombre`.

- **Contexto**: `subtitles.create` con `diarize` necesita la diarización que ya existe en 035 y su caché (D-5).
- **Elegida**: `create_main` llama a `run.diarize_file` con la carpeta `diarization/` del trabajo y etiqueta las palabras con `assign.assign_speakers`. Así la transcripción y la diarización van en el mismo proceso, que ya tiene el turno de la GPU. `from-transcript` lee el `speakers.json` del transcribe de 035.
- **Descartadas**: un trabajo `diarize` aparte (dos turnos de GPU y dos cargas de modelo); diarizar otra vez desde el documento.
- **Cómo comprobarla**: `test_ac2_las_palabras_toman_el_hablante_de_su_turno` y `test_ac2_from_transcript_con_hablantes`.

- **Contexto**: un `subtitles.create` con `diarize` de otro origen no tiene sentido ni motor.
- **Elegida**: la validación pide los hablantes de 035 (`speaker_errors`) y el motor solo para `origin: file`. Narración y limpiador no diarizan aquí (el limpiador lo hace en la fase 3).

- **Pendiente**: la corrida real con pyannote va en la verificación final (`PENDING/037-corrida-real` cubre el motor; el de esta fase se mide en la FV de 038).

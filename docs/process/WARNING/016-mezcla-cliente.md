# 016: cliente de Mezcla (T5)

**Qué se decidió.**

- **Entradas por el hash.** `#/mix?voice=…`, `?music=…` y `?video=…` cargan una ranura al abrir la sección (`shared/navigation/hash.ts`, que también abre secciones). `#/music?match=<archivo>&tail=<s>` iguala la duración de Música a la del archivo más la cola (`features/music/useMatchDuration.ts`).
- **Intro y outro al crear.** «Generar música para esta voz» manda `match` sin cola: intro y outro valen 0 por defecto en el server (`mix/project.py`). Si después cambian en el editor, la música ya generada no se recalcula.
- **«Mandar a Mezclar» en Música** envía la pista elegida con «Elegir»; sin elección queda deshabilitado. Antes estaba deshabilitado siempre.
- **«Mandar a Mezclar» en Narración** envía el `.wav` de la narración como voz.
- **Historial de video.** La ranura de video ofrece `clean.render`, `media.convert` y `subtitles.burn`: la spec no fija qué tipos de trabajo dejan video.
- **REFACTOR de `DurationField`.** No se cambia: sus «Igualar a…» son una lista de narraciones con su duración, no repiten el selector de `UIJobPicker`.
- **Textos.** `music.compare.mix` pasa a `mix.send` en los tres catálogos (solo la usaba Música). Las claves `mix.*` van en `server/src/content_studio/messages/`, que lee el client.
- **Atajos de la línea de tiempo.** Flechas mueven 0,1 s sin salir de la mezcla; Supr borra la región. Cada región es un botón con su nombre (`Región n`).
- **Inventario (AC-1).** `UIJobPicker` entra en `molecules/`; el icono `mix` es `SlidersHorizontal`.
- **Modo del video.** Con video en su ranura aparece «Cómo usar el video»: reemplazar su audio (por defecto) o mezclar por debajo. Va en `video_mode` al crear el proyecto.
- **Selector del historial con `emptyOption`.** `UISelect` con una sola opción no muestra selector: fija el valor y dispara `onChange` al montarse. Con un único trabajo terminado, la ranura se cargaba sola. El picker siempre muestra «Elige un trabajo…» y va con `value=""`, así que elegir el mismo trabajo otra vez también dispara `onChange`.
- **Tests de servidor (espejo).** `mix/test_mix_render.py` pasa a `mix/test_render.py` (espejo de `mix/render.py`) y absorbe `test_mix_video.py`, que era huérfano. Nuevos: `db/test_mix_projects.py`, `services/test_mix_render.py` (cobertura del servicio, 50 % antes) y `mix/test_project.py`.
- **Carga diferida.** `MixPage` se carga con `lazy` como Música, para no subir el presupuesto del arranque.

**Pendiente.** Arrastrar un archivo a una ranura y arrastrar regiones con el ratón: ver `docs/process/PENDING/016-arrastrar-a-ranura.md`.

**Dónde.** `client/src/features/mix/` (`MixPage`, `MixSlot`, `MixEditor`, `MixTimeline`, `useMixPreview`, `types`), `client/src/shared/components/molecules/UIJobPicker/`, `features/music/{MusicCompare,MusicPage,useMatchDuration}`, `features/narration/NarrationResult`, `app/{nav,Shell}`.

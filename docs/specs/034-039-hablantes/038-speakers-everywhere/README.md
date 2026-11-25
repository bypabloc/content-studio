# Spec 038: Hablantes en Subtítulos, Editor y Limpiador

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `038-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-038/` o `tmp/spec-038/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/038-speakers-everywhere` desde `origin/dev`, en `../content-studio-worktrees/038-speakers-everywhere/` |
| Depende de | 037 (y, por ella, 035 y 036) |
| Origen | Pedido del usuario (2026-11-24) |

## Objetivo

Que el hablante se vea donde ya se transcribe:

* **Subtítulos**: un cue nunca mezcla hablantes; cada uno lleva su etiqueta y su color en la vista previa y el quemado, y un prefijo opcional al exportar.
* **Editor**: los cues de la pista de subtítulos se dibujan con el color de su hablante.
* **Limpiador**: la transcripción de la revisión muestra el hablante de cada palabra.

En los tres hay un interruptor «Identificar hablantes».

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Hallazgos, decisiones, fuera de alcance y AC | Primero |
| [02-diseno.md](02-diseno.md) | Documento de subtítulos, ASS y exportación, parámetros y textos | Antes de la primera fase |
| [fases/1-subtitulos-server/](fases/1-subtitulos-server/plan-tdd.md) | Segmentación, documento, orígenes, ASS y exportación | Fase 1 |
| [fases/2-subtitulos-client/](fases/2-subtitulos-client/plan-tdd.md) | Interruptor, chip de hablante, leyenda y exportación | Fase 2 |
| [fases/3-editor-limpiador/](fases/3-editor-limpiador/plan-tdd.md) | Pista del Editor y revisión del Limpiador | Fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Corrida real, quemado y cierre | Con todos los commits hechos |

## Estado por fase

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Subtítulos: server](fases/1-subtitulos-server/plan-tdd.md) | C1, C2, C3 | AC-1, AC-2, AC-3, AC-4 | (ver historial de git) | IMP |
| F2 | [Subtítulos: client](fases/2-subtitulos-client/plan-tdd.md) | C4, C5 | AC-5, AC-6 | (ver historial de git) | IMP |
| F3 | [Editor y Limpiador](fases/3-editor-limpiador/plan-tdd.md) | C6, C7 | AC-7, AC-8 | (ver historial de git) | IMP |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | (ver historial de git) | IMP |

## Decisiones cerradas (no reabrir)

1. **D-1**: El documento de subtítulos sigue en `version: 1` con dos campos opcionales: `cue.speaker` y `document.speakers: {id: {name, color}}`. Un documento sin ellos se comporta como hoy (agente, 2026-11-24).
2. **D-2**: La segmentación corta siempre en un cambio de hablante, antes que en la puntuación (agente, 2026-11-24).
3. **D-3**: En ASS, el estilo `classic` y el `social` usan el color del hablante en el texto. En `social`, la palabra resaltada sigue con su color de resaltado. El modo `karaoke` no cambia (agente, 2026-11-24).
4. **D-4**: Exportar con «Incluir nombres» escribe `Ana: ` en el primer renglón del cue en SRT y `<v Ana>` en VTT. Viene apagado (agente, 2026-11-24).
5. **D-5**: El Limpiador diariza con `clean.analyze` y `diarize: true`, a través de `diarization.run.diarize_file` con caché. Los subtítulos que salen del Limpiador conservan los hablantes con el mismo `remap` que las palabras (agente, 2026-11-24).
6. **D-6**: En la línea de tiempo del Editor, el carril de una pista de subtítulos dibuja un bloque por cue: el color del hablante (o el neutro si no tiene) y el texto recortado. Es de solo lectura (agente, 2026-11-24).

## Reglas críticas

- Un proyecto de subtítulos, un análisis del Limpiador o un proyecto del Editor sin hablantes no cambia de comportamiento. Las fixtures de caracterización no se regeneran.
- El quemado usa los mismos colores que la vista previa (JASSUB y libass leen el mismo ASS).
- Textos en los tres catálogos.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `server/tests/unit/src/content_studio/subtitles/test_segment.py::test_ac1_corta_en_cambio_de_hablante` | proyecto real |
| AC-2 | F1 | C2 | `server/tests/unit/src/content_studio/subtitles/test_create_main.py::test_ac2_diarize_y_origenes` | proyecto real |
| AC-3 | F1 | C3 | `server/tests/unit/src/content_studio/subtitles/test_ass.py::test_ac3_color_por_hablante` y `client/tests/unit/src/features/subtitles/ass.test.ts` | cuadro del quemado (FV) |
| AC-4 | F1 | C3 | `server/tests/unit/src/content_studio/subtitles/test_formats.py::test_ac4_prefijo_srt_vtt` | archivo real |
| AC-5 | F2 | C4 | `client/tests/unit/src/features/subtitles/CueList.test.tsx` y `cues.test.ts` | e2e |
| AC-6 | F2 | C5 | `client/tests/unit/src/features/subtitles/SubtitlesPage.test.tsx` | e2e |
| AC-7 | F3 | C6 | `client/tests/unit/src/features/editor/timeline/SubtitleLane.test.tsx` y `SubtitleTracksPanel.test.tsx` | app-check |
| AC-8 | F3 | C7 | `server/tests/unit/src/content_studio/clean/test_analyze_main.py::test_ac8_diarize` y `client/tests/unit/src/features/cleaner/CleanReview.test.tsx` | app-check |

## WARNING y PENDING

- WARNING: `038-documento-con-hablantes` (D-1 y D-2), `038-ass-por-hablante` (D-3 y D-4), `038-limpiador-diariza` (D-5).
- PENDING: `038-corrida-real`, solo si falta el token del usuario.

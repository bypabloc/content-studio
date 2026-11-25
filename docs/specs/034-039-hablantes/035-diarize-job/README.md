# Spec 035: Trabajo `diarize` y transcripción con hablantes

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `035-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-035/` o `tmp/spec-035/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/035-diarize-job` desde `origin/dev`, en `../content-studio-worktrees/035-diarize-job/` |
| Depende de | 034 (receta `pyannote` y familia `diarization`) |
| Origen | Pedido del usuario (2026-11-24) · [investigación 03 a 05](../../../research/diarizacion-pyannote/README.md) |

## Objetivo

Dejar listo todo lo de servidor que usan las secciones de la 036 a la 038:

* **`diarize`**: turnos por hablante de un audio, con sus exportaciones y la caché;
* **`diarize.split`**: un audio por hablante;
* **`transcribe` con `diarize: true`**: el hablante de cada palabra;
* **`studio diarize`**: el mismo trabajo desde el CLI;
* la verificación de humo del motor.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Hallazgos, decisiones, fuera de alcance, AC y debe sonar | Primero |
| [02-diseno.md](02-diseno.md) | Flujo, salidas, API, CLI, caché y módulos | Antes de la primera fase |
| [fases/1-nucleo/](fases/1-nucleo/plan-tdd.md) | Unión palabra-hablante, bloques y exportaciones (stdlib) | Fase 1 |
| [fases/2-motor/](fases/2-motor/plan-tdd.md) | `diarize_main` en el venv, audio por hablante y verificación | Fase 2 |
| [fases/3-trabajos/](fases/3-trabajos/plan-tdd.md) | Servicios, caché, `transcribe` con hablantes y CLI | Fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Corridas reales, VRAM, escucha y cierre | Con todos los commits hechos |

## Estado por fase

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Unión, bloques y exportaciones](fases/1-nucleo/plan-tdd.md) | C1, C2 | AC-1, AC-2, AC-3 | - | IMP |
| F2 | [Motor en su venv y audio por hablante](fases/2-motor/plan-tdd.md) | C3, C4, C5 | AC-4, AC-5, AC-6 | - | PEN |
| F3 | [Trabajos, caché y CLI](fases/3-trabajos/plan-tdd.md) | C6, C7, C8 | AC-7, AC-8, AC-9, AC-10, AC-11 | - | PEN |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

1. **D-1**: La unión usa `exclusive_diarization`: cada palabra va al hablante con más solape y, en un hueco, al turno más cercano a 1 s o menos medido entre bordes. Si no hay ninguno, queda sin hablante (agente, 2026-11-24).
2. **D-2**: La diarización corre en su propio proceso y venv:
   * con `PYANNOTE_METRICS_ENABLED=0` y `HF_HUB_OFFLINE=1`;
   * con el pipeline cargado desde `models/community-1`;
   * con el audio en memoria (WAV 16 kHz mono leído con `wave` y numpy);
   * con `embedding_batch_size=4`.

   El valor del lote se ajusta con la medición de la FV (agente, 2026-11-24).
3. **D-3**: `transcribe` con `diarize: true` ejecuta, bajo un solo turno de GPU y en este orden:
   1. `transcribe_main`;
   2. `diarize_main`;
   3. la unión.

   Lo orquesta `diarization/transcribe_speakers_main.py`, que corre en la Python del server. Sin `diarize`, el comando es el de hoy (agente, 2026-11-24).
4. **D-4**: Caché propia de diarización: tabla `diarizations` (migración nueva) con ruta, mtime, tamaño y número de hablantes pedido. El JSON va en `<datos>/diarizations/<sha1>.json`. La caché de transcripción no cambia (agente, 2026-11-24).
5. **D-5**: El audio por hablante es un trabajo aparte de CPU, `diarize.split`:
   * con ffmpeg, un WAV por hablante con la misma duración y formato que el original;
   * silencio fuera de sus turnos, para mantener la sincronía (agente, 2026-11-24).
6. **D-6**: Nombres y colores de los hablantes:
   * viven en `speakers.json`, en la carpeta del trabajo;
   * los colores salen de una paleta fija de 8, asignada por orden de aparición;
   * las etiquetas `SPEAKER_00`… no se renombran en los demás archivos (agente, 2026-11-24).
7. **D-7**: No se diariza y se devuelve un solo hablante, `SPEAKER_00`, cuando el audio dura menos de 3 s, cuando se pide `num_speakers=1` o cuando no hay voz (agente, 2026-11-24).
8. **D-8**: `studio diarize <archivo> [--speakers N | --min-speakers A --max-speakers B]`, con una línea en `build_parser` (agente, 2026-11-24).

## Reglas críticas

- `diarization/assign.py`, `blocks.py`, `exports.py` y `cache.py` usan solo stdlib. torch, numpy y pyannote se importan dentro de `diarize_main`.
- Un modelo a la vez: la diarización nunca corre mientras Whisper sigue cargado. Son procesos en secuencia bajo el mismo candado.
- La telemetría de pyannote queda apagada siempre. Un test lo comprueba en el entorno del subproceso.
- El JSON de `transcribe` sin `diarize` no cambia (caracterización).
- Migración SQL que solo agrega.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `server/tests/unit/src/content_studio/diarization/test_assign.py::test_ac1_solape_hueco_y_lejos` | corrida real (FV) |
| AC-2 | F1 | C1 | `server/tests/unit/src/content_studio/diarization/test_blocks.py::test_ac2_corta_y_absorbe` | solo pytest |
| AC-3 | F1 | C2 | `server/tests/unit/src/content_studio/diarization/test_exports.py::test_ac3_rttm_csv_json` | archivos reales (FV) |
| AC-4 | F2 | C3 | `server/tests/unit/src/content_studio/diarization/test_diarize_main.py::test_ac4_entorno_y_salida` | corrida real con VRAM (FV) |
| AC-5 | F2 | C4 | `server/tests/unit/src/content_studio/diarization/test_speaker_audio.py::test_ac5_comando_ffmpeg` | duración, LUFS y escucha (FV) |
| AC-6 | F2 | C5 | `server/tests/unit/src/content_studio/engines/test_verification.py::test_ac6_familia_diarization` | `verify` real (FV) |
| AC-7 | F3 | C6 | `server/tests/unit/src/content_studio/services/test_diarize.py::test_ac7_validacion_y_comando` | trabajo real (FV) |
| AC-8 | F3 | C6 | `server/tests/unit/src/content_studio/diarization/test_cache.py::test_ac8_reusa_sin_modelo` | segunda corrida sin carga de modelo (FV) |
| AC-9 | F3 | C7 | `server/tests/unit/src/content_studio/diarization/test_transcribe_speakers_main.py::test_ac9_palabras_con_hablante` | trabajo real (FV) |
| AC-10 | F3 | C7 | `server/tests/integration/test_characterization.py::test_ac10_transcribe_sin_diarize_igual` | solo pytest |
| AC-11 | F3 | C8 | `server/tests/unit/src/content_studio/cli/test_diarize.py::test_ac11_parser_y_error` | `--help`, caso real y de error (FV) |

## WARNING y PENDING

- WARNING: `035-union-exclusiva` (D-1), `035-batch-de-embeddings` (D-2, con lo medido), `035-orquestador-transcribe` (D-3), `035-audio-por-hablante` (D-5).
- PENDING: `035-corrida-real`, solo si falta el token del usuario (`blocked — user-credential`).

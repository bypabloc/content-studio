# Spec 037: Sección Hablantes (solo diarizar)

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `037-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-037/` o `tmp/spec-037/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/037-speakers-section` desde `origin/dev`, en `../content-studio-worktrees/037-speakers-section/` |
| Depende de | 036 (`/jobs/{id}/speakers`, `UISpeakerLegend` y `UISpeakerCountField`) |
| Origen | Pedido del usuario (2026-11-24) |

## Objetivo

Una sección **Hablantes** para diarizar un audio o un video sin transcribir. Ofrece:

* la línea de tiempo con los turnos coloreados;
* nombres editables;
* exportar los turnos (JSON, RTTM y CSV);
* un audio por hablante;
* «Abrir en el Editor», con un marcador por turno.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Hallazgos, decisiones, fuera de alcance y AC | Primero |
| [02-diseno.md](02-diseno.md) | API, proyecto del Editor, pantalla y textos | Antes de la primera fase |
| [fases/1-api/](fases/1-api/plan-tdd.md) | Resultado de una diarización y proyecto del Editor | Fase 1 |
| [fases/2-seccion/](fases/2-seccion/plan-tdd.md) | Sección, línea de tiempo, archivos y audio por hablante | Fase 2 |
| [03-verificacion-final.md](03-verificacion-final.md) | Corrida real, escucha y cierre | Con todos los commits hechos |

## Estado por fase

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [API de diarización y proyecto del Editor](fases/1-api/plan-tdd.md) | C1, C2 | AC-4, AC-6 | - | PEN |
| F2 | [Sección Hablantes](fases/2-seccion/plan-tdd.md) | C3, C4, C5 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7 | - | PEN |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

1. **D-1**: Sección nueva `speakers` («Hablantes») en «Editar», justo después de Transcripción (usuario y agente, 2026-11-24).
2. **D-2**: La línea de tiempo usa WaveSurfer con regiones de solo lectura, una por turno de la diarización exclusiva, con el patrón de `ReviewWave.tsx` (agente, 2026-11-24).
3. **D-3**: «Abrir en el Editor» crea un proyecto v3 con el audio como clip y un marcador por turno exclusivo con el nombre del hablante. Los turnos de menos de 0,5 s no llevan marcador (agente, 2026-11-24).
4. **D-4**: Los archivos de turnos ya existen en la carpeta del trabajo (035). La sección los lista con «Abrir carpeta» y no copia nada a otro lado (agente, 2026-11-24).
5. **D-5**: «Solo este hablante» atenúa las demás regiones y salta de turno en turno con ← y →, sin generar audio (agente, 2026-11-24).

## Reglas críticas

- Las regiones no se arrastran: esta spec no edita turnos.
- El color nunca es la única señal: cada región lleva el nombre en su etiqueta.
- Textos en los tres catálogos; componentes en la jerarquía.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F2 | C3 | `client/tests/unit/src/features/speakers/SpeakersForm.test.tsx` | app-check |
| AC-2 | F2 | C4 | `client/tests/unit/src/features/speakers/SpeakerTimeline.test.tsx` | app-check con un trabajo real |
| AC-3 | F2 | C4 | `SpeakerTimeline.test.tsx::renombrar actualiza las etiquetas` | e2e |
| AC-4 | F1 | C1 | `server/tests/unit/src/content_studio/api/routes/test_diarizations.py::test_ac4_resultado_y_archivos` | archivos reales |
| AC-5 | F2 | C5 | `client/tests/unit/src/features/speakers/SpeakerFiles.test.tsx` | escucha de los WAV |
| AC-6 | F1 | C2 | `server/tests/unit/src/content_studio/editor/test_from_diarization.py::test_ac6_clip_y_marcadores` | Editor real |
| AC-7 | F2 | C3 | `SpeakersPage.test.tsx::from_job` | e2e |

## WARNING y PENDING

- WARNING: `037-seccion-hablantes` (D-1, D-3 y D-5).
- PENDING: `037-corrida-real`, solo si falta el token del usuario.

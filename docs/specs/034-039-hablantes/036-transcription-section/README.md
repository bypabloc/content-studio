# Spec 036: Sección Transcripción con «Identificar hablantes»

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `036-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-036/` o `tmp/spec-036/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/036-transcription-section` desde `origin/dev`, en `../content-studio-worktrees/036-transcription-section/` |
| Depende de | 035 (`transcribe` con `diarize` y `speakers.json`) |
| Origen | Pedido del usuario (2026-11-24) |

## Objetivo

Una sección propia **Transcripción** que:

* transcribe un archivo con el modelo y el idioma elegidos;
* con «Identificar hablantes», muestra el texto por turnos con nombre y color;
* permite renombrar hablantes, exportar el texto «Ana: …» y crear subtítulos desde el resultado.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Hallazgos, decisiones, fuera de alcance y AC | Primero |
| [02-diseno.md](02-diseno.md) | API, pantalla, componentes compartidos y textos | Antes de la primera fase |
| [fases/1-api/](fases/1-api/plan-tdd.md) | Transcripción, hablantes y exportación TXT | Fase 1 |
| [fases/2-seccion/](fases/2-seccion/plan-tdd.md) | Componentes de hablantes y sección | Fase 2 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, corrida real, app-check y cierre | Con todos los commits hechos |

## Estado por fase

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [API de transcripción y hablantes](fases/1-api/plan-tdd.md) | C1, C2 | AC-5, AC-6 | c3d9343 | IMP |
| F2 | [Sección Transcripción](fases/2-seccion/plan-tdd.md) | C3, C4, C5 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7 | (ver historial de git) | IMP |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

1. **D-1**: Sección nueva `transcription` en el grupo «Editar», antes de Limpiador (usuario, 2026-11-24).
2. **D-2**: Los hablantes se editan con `GET/PUT /jobs/{id}/speakers` sobre `speakers.json`. Sirve para trabajos `transcribe` y `diarize`, y la 037 la reusa (agente, 2026-11-24).
3. **D-3**: El TXT tiene un bloque por cambio de hablante, con `[hh:mm:ss] Nombre: texto`. Las marcas de tiempo son opcionales. Sin hablantes, va un párrafo por segmento. Se escribe en la carpeta del trabajo (agente, 2026-11-24).
4. **D-4**: Hay dos componentes compartidos:
   * `UISpeakerCountField` (automático, exacto o rango);
   * `UISpeakerLegend` (nombre editable y color).

   Los reusan la 037 y la 038 (agente, 2026-11-24).
5. **D-5**: La sección abre resultados anteriores con `?from_job=<id>` (`useFromJob`). No tiene un historial propio: la cola y la Biblioteca ya lo dan (agente, 2026-11-24).

## Reglas críticas

- Componentes en la jerarquía átomos, moléculas y organismos; `ui-structure` y la jerarquía de imports en verde.
- Textos en los tres catálogos.
- El color nunca es la única señal: cada bloque lleva también el nombre.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F2 | C4 | `client/tests/unit/src/app/nav.test.ts` | app-check smoke |
| AC-2 | F2 | C3, C4 | `client/tests/unit/src/features/transcription/TranscriptionForm.test.tsx` | e2e y corrida real |
| AC-3 | F2 | C4 | `TranscriptionForm.test.tsx::sin motor de diarización` | e2e |
| AC-4 | F2 | C5 | `client/tests/unit/src/features/transcription/TranscriptView.test.tsx` | app-check con un trabajo real |
| AC-5 | F1 | C1 | `server/tests/unit/src/content_studio/api/routes/test_speakers.py::test_ac5_get_put_valida` | e2e |
| AC-5 | F2 | C3 | `client/tests/unit/src/shared/components/molecules/UISpeakerLegend.test.tsx` | e2e |
| AC-6 | F1 | C2 | `server/tests/unit/src/content_studio/diarization/test_transcript_text.py::test_ac6_txt_por_turnos` | archivo real |
| AC-7 | F2 | C5 | `TranscriptView.test.tsx::crear subtítulos` | e2e |

## WARNING y PENDING

- WARNING: `036-seccion-transcripcion` (D-1 y D-5).
- PENDING: ninguna prevista.

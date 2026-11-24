# Spec 039: Verificación integral del lote de hablantes

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `039-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-039/` o `tmp/spec-039/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | chore |
| Escala | Micro (1–2 archivos de código: un escenario de app-check y la receta) |
| Rama | `chore/039-integral-verification` desde `origin/dev`, en `../content-studio-worktrees/039-integral-verification/` |
| Depende de | 038 |
| Origen | Cierre del lote 034–039 |

## Objetivo

Probar el lote entero con audio real en este equipo y fijar los números medidos en la receta y en la investigación. Al final, borrar la carpeta del lote.

## Contexto

Cada spec del lote se verificó por su cuenta. Falta lo transversal:

* que las cinco entradas (Transcripción, Hablantes, Subtítulos, Editor y Limpiador) den los mismos hablantes para el mismo archivo, gracias a la caché de la 035;
* la VRAM y el tiempo en la RTX 4060;
* la calidad en español con clips propios ([investigación 06 §4](../../../research/diarizacion-pyannote/06-calidad-y-evaluacion.md)).

## Precondición

```bash
git log origin/dev --merges --oneline | grep -q 'feature/038-speakers-everywhere' || echo FALLA
```

El motor `pyannote` debe estar instalado con el token del usuario. Si no lo está, esta spec se detiene con `blocked — user-credential`: es la única spec del lote que no puede cerrarse sin él.

## Decisiones

- **D-1**: Los números medidos reemplazan `size_gb` y `vram_gb` provisionales de `pyannote.json` (agente, 2026-11-24).
- **D-2**: Los resultados de las mediciones van a `docs/research/diarizacion-pyannote/10-pruebas-en-gpu.md`, enlazado desde el índice de la investigación (agente, 2026-11-24).

## Fuera de alcance

- Arreglos de funcionalidad. Si una comprobación falla, se corrige con un `fix:` en esta rama si es chico; si no, va a `PENDING/` con su spec futura.
- Ajustar hiperparámetros de pyannote.

## Criterios de aceptación

- **AC-1**: WHEN se diariza el mismo clip desde Hablantes, Transcripción, Subtítulos y el Limpiador THEN los cuatro muestran los mismos turnos, y solo la primera vez se carga el modelo (logs de los trabajos).
- **AC-2**: WHEN se diariza un clip de 30 min y otro de 60 min con `gpu-turn status` libre THEN:
  * el pico de VRAM medido con `nvidia-smi` queda en 3 GB o menos;
  * el tiempo por hora de audio queda anotado.
- **AC-3**: WHEN se evalúan los clips propios (al menos un diálogo de 2 personas y uno de 3) contra una referencia anotada a mano THEN el DER (sin collar y con collar de 0,25 s) y el WDER quedan en `10-pruebas-en-gpu.md`.
- **AC-4**: WHEN corre `python -m devtools app-check run --scenario=speakers` y el smoke THEN salen con exit 0, y `image-reader` revisa las capturas de Transcripción, Hablantes, Subtítulos, Editor y Limpiador en claro y oscuro.

## Ciclo y archivos

#### Ciclo C1: receta con lo medido [AC-2]

- **RED**: `server/tests/unit/src/content_studio/engines/test_recipes.py::test_ac2_pyannote_vram_medida` — `vram_gb` igual al valor medido, redondeado hacia arriba a 0,5 GB.
- **GREEN**: `server/src/content_studio/engines/recipes/pyannote.json`. Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`.

Archivos:

- Modificar `server/src/content_studio/engines/recipes/pyannote.json` (`size_gb` y `vram_gb`).
- Crear `docs/research/diarizacion-pyannote/10-pruebas-en-gpu.md` y enlazarlo desde el README de la investigación.
- Ajustar `tests/e2e/app-check/speakers.check.ts` si hace falta para recorrer las cinco secciones.
- Borrar `docs/specs/034-039-hablantes/` y su fila de `docs/specs/README.md`.

## Commit

```text
chore: verificación integral del lote de hablantes

- VRAM y tiempo medidos en la receta de pyannote; pruebas en GPU en la investigación
- cierre del lote 034-039
```

## Verificación final

1. `uv run ruff check && uv run ruff format --check`; `python -m devtools test-runner --type=all`; `uv run pytest -m local`; `python -m devtools test-runner --type=e2e`.
2. Las comprobaciones de AC-1 a AC-4, con las salidas en `tmp/spec-039/` y los logs en `logs/spec-039-*.log`.
3. Las fichas `PENDING/03x-corrida-real` que hayan quedado de la 034 a la 038 se cierran aquí, con sus resultados.
4. Las rutas de `out/` para escuchar (audios por hablante) y ver (video quemado) van al PR.
5. `git fetch origin dev`, un push, PR, checks, `gh pr merge --merge` y `worktree close 039-integral-verification`.

## WARNING y PENDING

- WARNING: `039-vram-medida` si el valor obliga a cambiar `embedding_batch_size`.
- PENDING: lo que no se pueda cerrar, con qué lo cierra.

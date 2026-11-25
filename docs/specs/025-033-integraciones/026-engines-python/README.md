# Spec 026: Venvs de los motores en la Python, torch y librerías más altas que soporte cada uno

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `026-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-026/` o `tmp/spec-026/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | chore |
| Escala | Large (11+ archivos: 14 recetas, instalador y Motores) |
| Rama | `chore/026-engines-python` desde `origin/dev`, en `../content-studio-worktrees/026-engines-python/` |
| Depende de | 025 (Python del server y piso calculado desde las recetas) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

Cada motor (TTS, música, whisper, visión y asistente) se instala con la Python más alta que soportan su librería y torch, y con sus paquetes, commits y revisiones de modelos al día. El piso del código compartido sube solo, y Motores avisa cuando una receta instalada quedó vieja; los venvs que ya tienes solo cambian cuando pulsas «Actualizar».

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC, debe sonar | Primero |
| [fases/1-huella-receta/](fases/1-huella-receta/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-narracion/](fases/2-narracion/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [fases/3-musica-y-resto/](fases/3-musica-y-resto/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 3 | Al implementar la fase 3 |
| [fases/4-piso/](fases/4-piso/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 4 | Al implementar la fase 4 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, escucha, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Huella de receta y «Actualizar» en Motores](fases/1-huella-receta/plan-tdd.md) | C1, C2 | AC-3, AC-7 | pendiente | IMP |
| F2 | [Recetas de narración](fases/2-narracion/plan-tdd.md) | C3 | AC-1, AC-2, AC-4 | pendiente | IMP |
| F3 | [Música, whisper, visión y asistente](fases/3-musica-y-resto/plan-tdd.md) | C4 | AC-1, AC-2, AC-4, AC-6 | pendiente | IMP |
| F4 | [Piso nuevo](fases/4-piso/plan-tdd.md) | C5 | AC-5 | pendiente | IMP |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | IMP |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: Por motor: la Python más alta (3.15 → 3.14 → …) con la que su librería instala y genera; torch en la última versión con wheel CUDA de esa Python (usuario, 2026-11-24).
2. **D-2**: Cada receta guarda su huella (sha256 del JSON) al instalar; Motores marca `outdated` si cambió y «Actualizar» reinstala con el trabajo `engine.install` existente (agente, 2026-11-24).
3. **D-3**: La verificación instala en una carpeta de motores aislada (`tmp/spec-026/engines`, con `storage.engines` de una base temporal), nunca sobre los venvs del usuario (agente, 2026-11-24).
4. **D-4**: Las revisiones de HF y los commits de git pasan al último que funcione; si el último cambia la salida para peor (duración, LUFS, voz en la música), se queda el anterior con su ficha WARNING (agente, 2026-11-24).
5. **D-5**: El piso de sintaxis (spec 025, D-2) se recalcula de las recetas nuevas; si sube, ruff, mypy y `test_structure.py` lo siguen en el mismo commit (agente, 2026-11-24).

## Reglas críticas

- Lo que carga un modelo va con `gpu-turn run` o con `studio` (toman el candado; `turno-gpu.md`); un motor a la vez.
- Nunca se reinstala ni se borra un venv o modelo del usuario: todo en la carpeta aislada de D-3.
- Cada receta conserva paquetes, commits y revisiones fijados (exactos); nada de rangos.
- La música es siempre instrumental: una revisión nueva con voz se descarta.
- Licencias: no se cambia de modelo ni de repo; si la licencia de una revisión nueva cambió, se queda la anterior y se registra.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F2 | C3 | `server/tests/unit/src/content_studio/engines/test_recipes.py::test_ac1_every_engine_below_pinned_python_has_warning` | 03 §2 |
| AC-1 | F3 | C4 | `server/tests/integration/test_venvs.py (-m local, con la carpeta aislada)` | 03 §2 |
| AC-2 | F2 | C3 | `server/tests/unit/src/content_studio/engines/test_recipes.py::test_ac1_every_engine_below_pinned_python_has_warning` | 03 §2 |
| AC-2 | F3 | C4 | `server/tests/integration/test_venvs.py (-m local, con la carpeta aislada)` | 03 §2 |
| AC-3 | F1 | C1 | `server/tests/unit/src/content_studio/engines/test_installer.py::test_ac3_changed_recipe_is_outdated` | solo pytest |
| AC-4 | F2 | C3 | `server/tests/unit/src/content_studio/engines/test_recipes.py::test_ac1_every_engine_below_pinned_python_has_warning` | 03 §2, paso 2 |
| AC-4 | F3 | C4 | `server/tests/integration/test_venvs.py (-m local, con la carpeta aislada)` | 03 §2 |
| AC-5 | F4 | C5 | `tests/validators/test_structure.py::test_ac3_piso_sale_de_las_recetas` | solo pytest |
| AC-6 | F3 | C4 | `server/tests/integration/test_venvs.py (-m local, con la carpeta aislada)` | 03 §2 |
| AC-7 | F1 | C2 | `client/tests/unit/src/features/engines/EngineCard.test.tsx` | e2e de la fase |

## WARNING y PENDING

- WARNING: una ficha `026-<motor>-version` por motor que no llegó a la Python más alta, con el paquete que lo impide; `026-huella-receta` (D-2).
- PENDING: `026-reintentar-<motor>` para cada motor que quedó por debajo, con qué lo cierra (una versión nueva de su librería).

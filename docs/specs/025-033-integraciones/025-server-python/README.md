# Spec 025: Server, devtools, CI e instalador en la Python más alta (3.15) con las dependencias al día

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `025-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-025/` o `tmp/spec-025/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | chore |
| Escala | Medium (6–10 archivos) |
| Rama | `chore/025-server-python` desde `origin/dev`, en `../content-studio-worktrees/025-server-python/` |
| Depende de | 023 (cierre del lote 001–023: esta spec toca el lock, la CI y las reglas de todo el repo) |
| Origen | Pedido del usuario (2026-11-24) · [`docs/research/integraciones-locales/`](../../../research/integraciones-locales/README.md) |

## Objetivo

El server, `devtools/`, la CI y el instalador corren en la Python estable más alta (3.15.2 hoy; si una dependencia no la soporta, 3.14, y así), con todas las dependencias de Python en su última versión. 3.10 dejó de recibir parches el 2026-10-01. El código que corre dentro de los venvs de los motores mantiene la sintaxis del motor más viejo hasta la 026.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC, debe sonar | Primero |
| [fases/1-version-unica/](fases/1-version-unica/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [fases/2-dependencias/](fases/2-dependencias/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 2 | Al implementar la fase 2 |
| [fases/3-instalador/](fases/3-instalador/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 3 | Al implementar la fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, comprobaciones, escucha, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [Versión única y piso de los motores](fases/1-version-unica/plan-tdd.md) | C1, C2 | AC-1, AC-2, AC-3, AC-7 | pendiente | IMP |
| F2 | [Dependencias de Python al día](fases/2-dependencias/plan-tdd.md) | C3 | AC-4, AC-5 | - | PEN |
| F3 | [Instalador con la Python nueva](fases/3-instalador/plan-tdd.md) | C4 | AC-6 | - | PEN |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: Python del server = la estable más alta que instalen todas sus dependencias en Windows: 3.15, si no 3.14, y así; una sola fuente, `.python-version` (usuario, 2026-11-24).
2. **D-2**: El piso de sintaxis del código compartido con los motores sale de las recetas (mínimo de sus `python`; hoy 3.10): ruff `target-version`, mypy `python_version` y `test_structure` usan ese piso (agente, 2026-11-24).
3. **D-3**: La CI corre una sola versión (la de `.python-version`); el piso se valida con ast, ruff y mypy, no con un segundo intérprete (agente, 2026-11-24).
4. **D-4**: Cada dependencia directa de Python pasa a su última versión con `uv lock --upgrade`, y su cota inferior en `pyproject.toml` sube a esa versión (usuario, 2026-11-24).
5. **D-5**: El instalador prepara la misma Python y recrea el venv del server si la versión cambió (agente, 2026-11-24).

## Reglas críticas

- Solo lo que piden los AC; nada de «Fuera de alcance».
- El código que relanza `use_venv` sigue compilando con el piso de las recetas (D-2): nada de sintaxis ni stdlib más nuevas en lo que importan los motores.
- Si 3.15 no se puede, se baja un escalón y se registra en `WARNING/025-python-escalon.md` con el paquete que lo impide, y una ficha `PENDING/` para reintentar.
- Una dependencia que cambia su API se adapta aquí; no se fija una versión vieja sin su ficha WARNING.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `tests/validators/test_python_version.py::test_ac1_venv_runs_pinned_version` | solo pytest |
| AC-2 | F1 | C1 | `tests/validators/test_python_version.py::test_ac2_versions_match` | solo pytest |
| AC-3 | F1 | C2 | `tests/validators/test_structure.py::test_ac3_floor_comes_from_recipes` | `uv run pytest -m local` y la corrida de 03 §2 |
| AC-4 | F2 | C3 | `tests/validators/test_python_version.py::test_ac4_cotas_iguales_al_lock` | solo pytest |
| AC-5 | F2 | C3 | `python -m devtools test-runner --type=all` | CI del PR en verde |
| AC-6 | F3 | C4 | `client/src-tauri/src/bootstrap/prepare.rs::tests::recreates_venv_when_python_changes` | `python -m devtools app-check run --binary=<instalador nuevo> --scenario=installed` |
| AC-7 | F1 | C2 | `server/tests/integration/test_venvs.py (-m local)` | `uv run pytest -m local` y la corrida de 03 §2 |

## WARNING y PENDING

- WARNING: `025-python-escalon` solo si no se pudo 3.15; `025-matriz-ci` (D-3).
- PENDING: la de reintento si se bajó de escalón; si la actualización resuelve `PENDING/004-httpx-deprecado.md`, esta spec la cierra.

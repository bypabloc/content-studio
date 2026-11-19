# 003: test-runner en devtools, tests espejo y validador de tamaño

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `003-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en `tmp/spec-003/` o `tmp/test-runner/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | chore |
| Escala | Large (unos 15 archivos nuevos de devtools y el movimiento de todos los tests del server) |
| Rama | `chore/003-test-runner` desde `origin/dev`, en `../content-studio-worktrees/003-test-runner/` |
| Depende de | [002](../002-english-cspell/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Que un solo comando, `python -m devtools test-runner --type=<tipos>`, corra todos los gates del repo, igual en el pre-commit, el pre-push y la CI. Los gates son lint, spelling, validators (tamaño), typecheck, unit (espejo, cobertura ≥ 80 % y docstrings), tdd y guard-tdd. Los tests del server pasan a la ruta espejo del código que prueban.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Validador de tamaño con baseline | PEN |
| 2 | Espejo: mover los tests y la auditoría | PEN |
| 3 | Cobertura, docstrings y typecheck | PEN |
| 4 | test-runner que los une a todos, y gates en los hooks y la CI | PEN |

## Decisiones clave

* D-1: `devtools/test_runner/` con una etapa por módulo y un dict `STAGES`. La 005 le suma las etapas del client.
* D-2: límites en `tests/validators/file-size.json` (source 300, tests 800, instrucciones 300) y `file-size.baseline.json`, que no puede crecer.
* D-3: espejo en `server/tests/unit/src/content_studio/...`. Lo que cruza módulos va a `server/tests/integration/`, que queda fuera de la auditoría.
* D-4: pytest-cov con 80 % por archivo tocado. mypy para el typecheck. ruff `D1` para los docstrings.

## WARNING y PENDING

* WARNING: `003-baselines.md` (qué archivos entran en los baselines de tamaño, espejo y cobertura, y por qué).
* PENDING: `003-bajar-baselines.md` (vaciar los baselines a medida que se tocan los archivos).

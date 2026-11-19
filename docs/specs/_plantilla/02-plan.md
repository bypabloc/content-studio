# <NN>: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Ciclos TDD

Ordenados por dependencia (utilidades → parser y registro → motor o comando → CLI), de 1 a 8 por spec. Todo AC queda cubierto por al menos un ciclo; un fix empieza con un test de regresión.

#### Ciclo 1: <pieza> [AC-1]

- **RED**: `server/tests/test_<área>.py::test_ac1_<caso>` (o un doctest en `<módulo>`): WHEN <acción> THEN <resultado> [AC-1]. Falla por <motivo esperado>.
- **GREEN**: <implementación mínima>. Verify: `uv run pytest server/tests/test_<área>.py::test_ac1_<caso> -q`.
- **REFACTOR**: <mejora con la red en verde> · ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/<…>.py` | `uv run pytest server/tests/test_<área>.py -q` |
| Modificar | `server/src/content_studio/<…>/registro.py` | `uv run pytest server/tests/test_registro.py -q` |

Cada `.py` queda en 300 líneas o menos (`codigo-python.md`).

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | <…> | AC-1 | — | <comando> | [ ] |

Una tarea que carga un modelo tiene Verify «verificación final».

## 4. Commits

En Conventional Commits en español, en orden; cada uno deja verde `uv run ruff check`, `uv run ruff format --check` y `uv run pytest`.

1. `<tipo>: <qué>` — T1.

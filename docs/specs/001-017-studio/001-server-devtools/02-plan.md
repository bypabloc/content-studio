# 001: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Excepción pedida: `move-data` mueve `narration/` y `music/` a `server/data/`.

## 1. Ciclos TDD

Antes del ciclo 1: `uv run pytest -q --co | tail -1` en `dev` y anota la cantidad en el handoff (base de AC-1).

#### Ciclo 1: devtools fuera del paquete [AC-3]

- **RED**: `devtools/tests/test_devtools.py::test_ac3_help_lista_comandos`. WHEN `python -m devtools --help` corre desde la raíz THEN el stdout incluye los cinco comandos y sale con exit 0 [AC-3]. Falla porque `devtools/` no existe.
- **GREEN**: `git mv src/content_studio/devtools devtools` y `git mv tests/test_devtools.py devtools/tests/`. Agrega `devtools/rutas.py` con `RAIZ = Path(__file__).resolve().parents[1]` y reemplaza los imports de `content_studio.rutas` y `content_studio.devtools.*` por los relativos al paquete. Agrega una línea `move-data` en `COMANDOS`. Verify: `uv run pytest devtools/tests -q`.
- **REFACTOR**: ninguno.

#### Ciclo 2: move-data [AC-4]

- **RED**: `devtools/tests/test_move_data.py` con cuatro casos en `tmp_path`: plan sin `--apply`, mover con reescritura del `.pth` y de `direct_url.json`, idempotencia y destino ocupado (exit 1) [AC-4]. Falla porque falta `devtools/move_data.py`.
- **GREEN**: `devtools/move_data.py` con `main(argv)`. `plan(root)` devuelve la lista de movimientos, `apply(root)` hace `os.replace` por carpeta y busca en `server/data/**/.venv*/Lib/site-packages/` (también `lib/python*/site-packages` en POSIX) los `*.pth` y `*.dist-info/direct_url.json` que contengan el prefijo viejo, y reemplaza el texto. El stdout es JSON en una línea y el log va a stderr (`devtools.md` §2). Verify: `uv run pytest devtools/tests/test_move_data.py -q`.
- **REFACTOR**: si `worktree.py` ya tiene un helper para recorrer los venvs, reutilízalo.

#### Ciclo 3: workspace y código a server/ [AC-1, AC-2]

- **RED**: `tests/validators/test_estructura.py` (movido desde `tests/` y adaptado). Comprueba que no exista `src/` en la raíz, que el producto esté en `server/src/content_studio/`, que `cli.py` sea el único `.py` de la raíz y que no haya `.py` en `server/data/` [AC-2]. Falla porque `src/` sigue en la raíz.
- **GREEN**: `git mv src server/src` y `git mv tests server/tests` (después saca `test_estructura`, `test_hooks` y `test_handoff` a su lugar, ciclo 6). Crea `server/pyproject.toml` (paquete) y convierte el de la raíz en workspace (D-1). Corre `uv lock`. Verify: `uv sync && uv run pytest -q`.
- **REFACTOR**: el test de `test_estructura` que compara las dependencias de `cli.py` con `pyproject.toml` pasa a leer `server/pyproject.toml`.

#### Ciclo 4: rutas a server/data/ [AC-2, AC-6]

- **RED**: el doctest de `server/src/content_studio/rutas.py`: `>>> NARRATION.parent.name, (RAIZ / 'cli.py').is_file()` → `('data', True)`. Falla porque `RAIZ` todavía es `parents[2]`.
- **GREEN**: D-4. `git mv narration music server/data/` solo para lo versionado; lo no versionado lo mueve `move-data` en la verificación final. Actualiza `cli.py` (D-6) y `ruff.extend-exclude` (`server/data/narration/motores`, `server/data/music/models`). Verify: `uv run pytest -q` y `python cli.py --help | cat`.
- **REFACTOR**: `graphify query "NARRATION MUSIC RAIZ"` para encontrar rutas armadas a mano y pasarlas a `rutas`.

#### Ciclo 5: worktree prepare y close con las rutas nuevas [AC-8]

- **RED**: en `devtools/tests/test_devtools.py`, los casos de prepare y close esperan los enlaces en `server/data/...` [AC-8]. Fallan porque `worktree.py` enlaza `narration/...`.
- **GREEN**: cambia en `worktree.py` la lista de enlaces y la copia de audios de referencia. Verify: `uv run pytest devtools/tests -q`.
- **REFACTOR**: ninguno.

#### Ciclo 6: tests junto a sus hooks [AC-1]

- **RED**: ninguno nuevo. Es un movimiento: `git mv` de `test_hooks.py` a `.claude/hooks/tests/` y de `test_handoff.py` a `.agents/hooks/tests/`, ajustando el `sys.path` que agregan a sus hooks. La red es AC-1: el mismo total de tests.
- **GREEN**: `testpaths` de D-1. Verify: `uv run pytest -q --co | tail -1` igual a la base.
- **REFACTOR**: ninguno.

#### Ciclo 7: sin rutas viejas en reglas, hooks y CI [AC-7, AC-9]

- **RED**: `tests/validators/test_estructura.py::test_ac7_sin_rutas_viejas`. Hace `git ls-files` (sin `docs/research/` ni `docs/specs/`) y ningún archivo debe contener los patrones de AC-7. Falla con unos 45 archivos.
- **GREEN**: actualiza `.agents/rules/*`, `.agents/skills/*`, `.agents/hooks/handoff_text.py`, `.claude/hooks/session_start.py`, `graphify_guard.py` (rutas de código: `server/src`, `devtools`), `.claude/agents/*.md`, `.claude/settings.json`, `.git-hooks/pre-commit` (`python -m devtools contexto-agentes` y `reglas`), `.gitignore` (D-7), `.github/workflows/calidad.yml` (sin cambios de comandos; comprueba que pase), `AGENTS.md` (árbol y atajos), `server/data/narration/README.md`, `server/data/music/README.md`, `docs/process/01-done/*.md` y las plantillas de `docs/specs/_plantilla/`. Después, `python -m devtools reglas --sincronizar`. Verify: `uv run pytest tests/validators -q`, `python -m devtools contexto-agentes` y `python -m devtools reglas`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Mover | `src/content_studio/devtools/` → `devtools/` | `uv run pytest devtools/tests -q` |
| Crear | `devtools/rutas.py`, `devtools/move_data.py`, `devtools/tests/test_move_data.py` | ídem |
| Mover | `src/` → `server/src/`, `tests/` → `server/tests/` | `uv run pytest -q` |
| Crear | `server/pyproject.toml` | `uv sync` |
| Modificar | `pyproject.toml` (workspace), `uv.lock` | `uv sync && uv run ruff check` |
| Modificar | `server/src/content_studio/rutas.py`, `cli.py` | doctest y `python cli.py --help \| cat` |
| Mover | `narration/`, `music/` (lo versionado) → `server/data/` | `git status` |
| Mover | `test_estructura.py` → `tests/validators/`, `test_hooks.py` → `.claude/hooks/tests/`, `test_handoff.py` → `.agents/hooks/tests/` | `uv run pytest -q --co` |
| Modificar | `devtools/worktree.py` | `uv run pytest devtools/tests -q` |
| Modificar | Reglas, skills, hooks, `.git-hooks/pre-commit`, `.gitignore`, `.claude/settings.json`, `AGENTS.md`, README de datos, `docs/process/01-done/`, plantillas | `test_ac7_sin_rutas_viejas`, `contexto-agentes`, `reglas` |
| Crear | `docs/process/WARNING/001-move-data.md` y su fila | — |

Cada `.py` queda en 300 líneas o menos.

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | devtools a la raíz | AC-3 | — | `uv run pytest devtools/tests -q` | [ ] |
| T2 | `move_data.py` y su test | AC-4 | T1 | `uv run pytest devtools/tests/test_move_data.py -q` | [ ] |
| T3 | Workspace y `server/` | AC-1, AC-2 | T1 | `uv sync && uv run pytest -q` | [ ] |
| T4 | Rutas, `cli.py` y datos versionados | AC-2, AC-6 | T3 | `uv run pytest -q`, `python cli.py --help \| cat` | [ ] |
| T5 | Worktree prepare y close | AC-8 | T4 | `uv run pytest devtools/tests -q` | [ ] |
| T6 | Tests junto a sus hooks | AC-1 | T3 | `uv run pytest -q --co \| tail -1` | [ ] |
| T7 | Reglas, hooks, CI, `.gitignore` y docs | AC-7, AC-9 | T4–T6 | `uv run pytest tests/validators -q`, `contexto-agentes`, `reglas` | [ ] |
| T8 | Migración real y corridas | AC-4, AC-5, AC-6 | T7 | verificación final | [ ] |

## 4. Commits

En orden; cada uno deja verdes `uv run ruff check`, `uv run ruff format --check` y `uv run pytest`.

1. `refactor: devtools sale del paquete a devtools/ en la raíz` (T1).
2. `feat: devtools move-data mueve narration/ y music/ a server/data/ y corrige las rutas de las instalaciones editables` (T2).
3. `refactor: código Python a server/ con uv workspace en la raíz` (T3).
4. `refactor: rutas de datos a server/data/ y cli.py apunta a server/src` (T4).
5. `refactor: worktree prepare y close enlazan server/data/` (T5).
6. `test: tests de hooks junto a sus hooks y validador de estructura en tests/validators/` (T6).
7. `docs: reglas, skills, hooks, CI y README con las rutas nuevas` (T7, más la ficha WARNING).

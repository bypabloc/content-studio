# 002: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. Excepción pedida: `move-data` renombra datos a inglés.

## 1. Ciclos TDD

#### Ciclo 1: cspell y `devtools spelling` [AC-1, AC-2]

- **RED**: `devtools/tests/test_spelling.py`. Con un `.py` de fixture en `tmp_path`, informa los identificadores en español y no informa los docstrings ni los comentarios [AC-2]. Falla porque no existe el comando.
- **GREEN**: `package.json` y `bun.lock` (D-2), `cspell.config.yaml` y `devtools/cspell/content-studio-terms.txt` (D-1), y `devtools/spelling.py` con `main(argv)` más su línea en `COMANDOS`. Verify: `uv run pytest devtools/tests/test_spelling.py -q`. Si `bun` falta en CI, el test se marca `skipif(shutil.which('bun') is None)` y la CI instala bun.
- **REFACTOR**: ninguno.

#### Ciclo 2: gate en pre-commit y CI [AC-3]

- **RED**: un test que crea un repo git temporal con el hook y un archivo staged con `def calcular_total()`, y espera que el commit falle con la palabra en el stderr [AC-3].
- **GREEN**: `.git-hooks/pre-commit` llama a `python -m devtools spelling --staged` si hay archivos que cspell revisa. `calidad.yml` suma setup-bun, `bun install --frozen-lockfile` y `python -m devtools spelling`. En este ciclo, `ignorePaths` incluye temporalmente `server/src/**`, `devtools/**` y `.agents/hooks/**`, y cada ciclo siguiente saca una carpeta de la lista (ahí está la red de cada traducción).
- **REFACTOR**: ninguno.

#### Ciclo 3: migración de datos, paso 2 [AC-4]

- **RED**: en `devtools/tests/test_move_data.py`, los casos del paso 2. Sobre un árbol falso con `voz/experta.wav`, `voz/tomas/`, `voces/catalogo.json`, `motores/index-tts/.venv/...pth` y `docs/guiones/`, quedan los nombres nuevos con los mismos bytes, el `.pth` se reescribe y la operación es idempotente. Si un destino ya existe, sale con exit 1 [AC-4].
- **GREEN**: `MIGRATIONS` con los pasos 1 y 2 (D-4), y la tabla de estilos y emociones en un solo lugar (`server/src/content_studio/narration/styles.py`, que el paso 2 importa leyendo el JSON o un dict de datos sin depender del paquete). `git mv` de lo versionado.
- **REFACTOR**: si la tabla de renombres de estilos queda duplicada entre devtools y server, que viva en un `.json` de datos que lean los dos.

#### Ciclo 4: common, paths, narration y alias del guion [AC-5, AC-1]

- **RED**: `server/tests/test_script.py::test_ac5_alias_pause_text` [AC-5]. Se saca `server/src/content_studio/{common,narration}` (salvo `grabar/`) de `ignorePaths`, y `spelling` falla con la lista de palabras.
- **GREEN**: D-7 para `comun/`, `rutas.py` y `narration/` (motores, texto, evaluación, voces, pipeline, parser y estilos), y D-5 para los alias. Verify: `uv run pytest -q` y `python -m devtools spelling`.
- **REFACTOR**: `graphify update .` y `graphify query` para encontrar los usos que quedaron con el nombre viejo.

#### Ciclo 5: music y comandos del CLI, con flags en inglés [AC-6, AC-1]

- **RED**: `server/tests/test_cli.py::test_ac6_flags_en_ingles`. `--help` no contiene `--modelo` y `--modelo` sale con exit 2 [AC-6]. Se saca `music/` y `cli/commands/` de `ignorePaths`.
- **GREEN**: D-7 para `music/` y D-6 en los parsers de narration y music. `cli/` y `grabar/` se ajustan solo en imports y flags (D-3). Verify: `uv run pytest -q`, `python cli.py music --help | cat` y `spelling`.
- **REFACTOR**: ninguno.

#### Ciclo 6: devtools, hooks y tests [AC-1, AC-9]

- **RED**: se saca `devtools/`, `.agents/hooks/`, `.claude/hooks/` y los `tests/` de `ignorePaths`, y `spelling` falla.
- **GREEN**: D-7 para devtools (los comandos `gpu-turn`, `agent-context` y `rules`) y los hooks, más el nombre de cada test. `.claude/settings.json` y `.agents/hooks.json` apuntan a los nombres nuevos. Verify: `uv run pytest -q` y `spelling`.
- **REFACTOR**: ninguno.

#### Ciclo 7: fixtures de caracterización [AC-7]

- **RED**: las fixtures de `server/tests/fixtures/` fallan solo por las claves en inglés.
- **GREEN**: regenera las fixtures en un commit aparte (`codigo-python.md`, «Antes de cada commit») y revisa que el diff solo cambie nombres de claves y valores de estilo según la tabla.
- **REFACTOR**: ninguno.

#### Ciclo 8: reglas, docs y sin exclusiones de más [AC-9, AC-1]

- **RED**: `spelling` sobre todo lo versionado, con `ignorePaths` limitado a D-1 y D-3.
- **GREEN**: D-8. Se reescribe `textos-e-idioma.md` y se actualizan `codigo-python.md`, `devtools.md`, `graphify.md`, `verify-before-claiming-done.md`, `turno-gpu.md`, `command-output.md`, `worktrees.md`, `AGENTS.md`, los README de datos, `formato-guion.md`, `docs/process/01-done/` y las plantillas. Después, `python -m devtools rules --sync`. Verify: `spelling`, `agent-context` y `rules`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `package.json`, `bun.lock`, `cspell.config.yaml`, `devtools/cspell/content-studio-terms.txt`, `devtools/spelling.py`, `devtools/tests/test_spelling.py` | `uv run pytest devtools/tests -q` |
| Modificar | `.git-hooks/pre-commit`, `.github/workflows/calidad.yml`, `.gitignore` (`node_modules/`) | test del gate y CI |
| Modificar | `devtools/move_data.py`, `devtools/tests/test_move_data.py` | `uv run pytest devtools/tests/test_move_data.py -q` |
| Renombrar y modificar | todo `server/src/content_studio/**` salvo `cli/` (sin contar `commands/`) y `grabar/` | `uv run pytest -q`, `spelling` |
| Crear | `server/src/content_studio/narration/script_aliases.json`, `server/tests/test_script.py` | `uv run pytest server/tests/test_script.py -q` |
| Renombrar | `devtools/*`, hooks y tests | `uv run pytest -q` |
| Mover (`git mv`) | lo versionado de `server/data/narration/{voz,voces,docs/guiones}` | `git status` |
| Modificar | reglas, skills, `AGENTS.md`, README, `formato-guion.md`, `docs/process/` | `agent-context`, `rules` |
| Crear | `docs/process/WARNING/002-mapeo-de-nombres.md`, `docs/process/PENDING/002-cspell-excepciones-temporales.md` y sus filas | — |

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | cspell, bun y `spelling` | AC-1, AC-2 | — | `uv run pytest devtools/tests/test_spelling.py -q` | [ ] |
| T2 | Gates en pre-commit y CI | AC-3 | T1 | test del gate | [ ] |
| T3 | `move-data`, paso 2 | AC-4 | — | `uv run pytest devtools/tests/test_move_data.py -q` | [ ] |
| T4 | common, paths, narration y alias | AC-5 | T2, T3 | `uv run pytest -q`, `spelling` | [ ] |
| T5 | music y flags | AC-6 | T4 | ídem | [ ] |
| T6 | devtools, hooks y tests | AC-1 | T5 | ídem | [ ] |
| T7 | Fixtures | AC-7 | T6 | `uv run pytest -q` | [ ] |
| T8 | Reglas y docs | AC-9 | T7 | `spelling`, `agent-context`, `rules` | [ ] |
| T9 | Migración real y corridas | AC-4, AC-8 | T8 | verificación final | [ ] |

## 4. Commits

1. `chore: cspell de klinikae con bun y devtools spelling` (T1).
2. `ci: spelling en pre-commit y en calidad` (T2).
3. `feat: move-data renombra los datos de narración a inglés` (T3).
4. `refactor: common, paths y narration en inglés, con alias [pausa]/texto en el guion` (T4).
5. `refactor: music y flags del CLI en inglés` (T5).
6. `refactor: devtools, hooks y tests en inglés` (T6).
7. `test: regenerar fixtures de caracterización con las claves en inglés` (T7).
8. `docs: textos-e-idioma, reglas y README con el código en inglés` (T8 y las fichas).

# Spec 025: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `025-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-025/` o `tmp/spec-025/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

## 1. Precondición

La 023 cierra el lote 001–023. Antes del primer commit:

```bash
git fetch origin dev
git log origin/dev --merges --oneline | grep -q 'chore/023-integral-verification' || echo FALLA
git cat-file -e origin/dev:docs/specs/001-017-studio/README.md && echo FALLA   # la 023 borra la carpeta del lote
uv python list 3.15   # la versión disponible para uv
```

## 2. Contexto

El server corre hoy en la Python que elige `uv` (sin `.python-version`), con `requires-python = ">=3.10"` en `server/pyproject.toml`; la CI prueba 3.10 y 3.12 y el instalador prepara 3.12. El mínimo 3.10 existe porque los módulos de narración y música se relanzan en el venv de cada motor y CosyVoice usa 3.10. Python 3.10 llegó a su fin de vida el 2026-10-01 y la última estable es 3.15.2 (2026-10-25, [endoflife.date](https://endoflife.date/python)). Las integraciones (026–032) necesitan paquetes que ya exigen 3.11 (`fastmcp`, `watchdog` 7, `zeroconf`; investigación §1).

### Términos

| Término | Significado | En el código |
| :--- | :--- | :--- |
| Python del server | La del venv de `uv sync`: server, API, worker, CLI y devtools | `.python-version` |
| Piso | La Python más vieja entre los venvs de los motores; el código que corre dentro de ellos no puede usar nada más nuevo | `python` de `server/src/content_studio/engines/recipes/*.json` |
| Escalón | Bajar a la versión anterior si una dependencia no tiene wheel de Windows para la nueva | D-1 |

### Hallazgos de la exploración

- **Tres versiones distintas hoy.** `PYTHON = "3.12"` en `client/src-tauri/src/bootstrap/prepare.rs`; `python: ['3.10', '3.12']` en `.github/workflows/calidad.yml`; `target-version = "py310"` y `python_version = "3.10"` en `pyproject.toml`.
- **El código corre dentro de los motores.** `use_venv` y `env_src` en `server/src/content_studio/common/process.py` relanzan con `PYTHONPATH=server/src`.
- **Pisos de las recetas** (medido el 2026-11-24): `cosyvoice3` y `heartmula` 3.10, `indextts` 3.11, el resto 3.12.
- **Dependencias directas del server**: `fastapi>=0.162.5`, `uvicorn>=0.54.0`, `send2trash>=2.2.0`; dev: `pytest>=8`, `ruff`, `numpy`, `soundfile`, `pytest-cov>=7.1.0`, `mypy>=2.4.1`, `httpx>=0.28.1` (`pyproject.toml` y `server/pyproject.toml`).
- **`test_structure.py`** compila con «la gramática de 3.10 (CosyVoice corre en 3.10)», un valor fijo (`tests/validators/test_structure.py`).
- **torch 2.15.0 publica wheels cp311 a cp315** (PyPI, 2026-11-24): no bloquea la 026.

## 3. Solución

- `.python-version` en la raíz con la versión elegida (D-1); `requires-python`, la CI y `prepare.rs` la siguen, y un test lo comprueba.
- Un helper de devtools calcula el piso desde las recetas y lo usan `test_structure.py` y un test que compara ruff y mypy (D-2).
- `uv lock --upgrade`, cotas iguales al lock y las adaptaciones que exijan las versiones nuevas (D-4).
- El instalador recrea el venv si la Python cambió (D-5).

Cada decisión pasa por la escalera de plan-format.md §0 (¿debe existir? ¿ya existe? ¿stdlib o una dependencia que ya está?).

- **D-1: Una sola versión de Python para server, devtools, CI e instalador, en `.python-version`** — El usuario pidió la más alta disponible. `uv` lee `.python-version`, y los demás lugares (`requires-python`, la CI, `PYTHON` de `prepare.rs`) se comprueban contra ese archivo con un test. Se descarta fijar la versión en cada archivo por separado, porque hoy ya divergen (`prepare.rs` usa 3.12 y la CI 3.10 y 3.12).
- **D-2: Piso de sintaxis calculado desde las recetas** — `use_venv` relanza los módulos en el venv de cada motor con `PYTHONPATH=server/src` (`common/process.py`, `env_src`): ese código corre con la Python del motor. mypy con `python_version` del piso detecta APIs de la stdlib que no existen ahí; ruff y `ast` con `feature_version`, la sintaxis. Se descarta subir el piso ya a 3.15, porque CosyVoice y HeartMuLa siguen en 3.10 hasta la 026.
- **D-3: Matriz de CI de una versión** — Con `requires-python` en 3.15, `uv sync` no puede crear un venv 3.10 con fastapi; lo que la matriz 3.10 probaba (que compile) lo cubre D-2. Se descarta mantener 3.10 en la matriz, porque exigiría dejar `requires-python` en 3.10 y no deja usar la sintaxis nueva en el server.
- **D-4: Dependencias al día y cotas iguales al lock** — Es software nuevo y el usuario pidió lo más actual. Con la cota igual al lock, un `uv lock` futuro no puede bajar una versión sin que el test lo note. Se descarta solo `uv lock --upgrade` sin tocar las cotas, porque deja `fastapi>=0.162.5` aunque el lock tenga otra.
- **D-5: Instalador con la versión de `.python-version`** — `PYTHON` de `client/src-tauri/src/bootstrap/prepare.rs` es 3.12; una actualización de la app con otra versión debe recrear el venv en el primer arranque. Se descarta pedir al usuario que reinstale, porque el updater (spec 022) es silencioso.

## 4. Fuera de alcance

- Los venvs de los motores (spec 026) y las dependencias del client y de Rust (spec 027).
- Usar sintaxis nueva en el código compartido con los motores antes de que la 026 suba el piso.
- Cambiar `uv` por otro gestor.

## 5. Criterios de aceptación

- **AC-1**: WHEN se corre `uv sync` en un clon limpio THEN el venv usa la versión de `.python-version` (3.15.x, o el escalón registrado en WARNING).
- **AC-2**: WHEN cambia la versión en `.python-version` THEN un test falla si `requires-python`, la matriz de `calidad.yml` o `PYTHON` de `prepare.rs` no coinciden.
- **AC-3**: Given las recetas de motores When se calcula el piso Then es el mínimo de sus `python` (hoy 3.10), y ruff `target-version`, mypy `python_version` y la compilación de `test_structure.py` usan ese piso.
- **AC-4**: WHEN se lee `pyproject.toml` y `server/pyproject.toml` THEN la cota inferior de cada dependencia directa es la versión del `uv.lock`, y `uv lock --upgrade` no cambia ninguna versión directa el día del merge.
- **AC-5**: WHEN se corre `python -m devtools test-runner --type=all` en la Python nueva THEN pasa, igual que la CI del PR.
- **AC-6**: Given una app instalada con el venv en 3.12 When el updater instala esta versión y arranca Then el bootstrap instala la Python nueva y recrea el venv del server antes de levantarlo.
- **AC-7**: WHEN el server en la Python nueva corre `uv run studio narration tts` con un motor de 3.12 y `music` con uno de 3.10 THEN ambos trabajos terminan y dejan su audio en `out/`.

## 6. Debe sonar / no debe sonar

| Salida | Debe | No debe |
| :--- | :--- | :--- |
| `out/narration/<…>-spec-025/` (Qwen 0.6B, texto corto) | La misma duración y LUFS que antes del cambio (±0,5 LU) | Cortes, silencio o error del relanzamiento |
| `out/music/<…>-spec-025/` (HeartMuLa, 30 s) | 30 s ±0,5, instrumental | Voz, clipping |

# 022: los recursos del instalador solo en el build de release

- **Contexto**: `tauri-build` exige que existan los recursos de `bundle.resources`; `cargo check`, `tauri dev` y la CI no arman `client/src-tauri/bundle/`.
- **Elegida**: `bundle.resources` y `createUpdaterArtifacts` van en `client/src-tauri/tauri.bundle.json`, que solo suma el build del instalador (`tauri build --config src-tauri/tauri.bundle.json`). El server va en `app/server/` con `pyproject.toml` y `uv.lock` del workspace en `app/`, para que el primer arranque haga `uv sync --frozen --project app` con el mismo lock (AC-6 decía `server/` en la raíz del bundle).
- **Descartadas**: crear carpetas vacías para `cargo check` (se colarían en un instalador incompleto); copiar solo `server/` sin el lock (el venv instalado no sería el probado).
- **Cómo revertir**: mover `resources` a `tauri.conf.json` y armar `bundle/` antes de cada compilación.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_bundle.py` y el listado del instalador en la verificación final.
- **Pendiente**: ninguno.

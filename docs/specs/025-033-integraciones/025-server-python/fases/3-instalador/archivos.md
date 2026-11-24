# Spec 025, fase 3: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## client/src-tauri/

### Modificar

- `client/src-tauri/src/bootstrap/prepare.rs` — `PYTHON` desde `.python-version`; recrea el venv del server si su versión difiere.
  - Verify: `python -m devtools test-runner --type=tauri-check`
- `client/src-tauri/build.rs` — lee `.python-version` (si se elige generarlo).

### Solo lectura

- `docs/operations/release.md` — cómo se publica para probar la actualización.

# 034: token de Hugging Face en `settings`, sin cifrar

- **Contexto**: el token se guarda en la tabla `settings` (clave `secret.huggingface.token`), que es SQLite local y no está cifrada. La API genérica lo bloquea con 403 y nunca lo devuelve.
- **Elegida**: `settings` con la clave `secret.*` (D-2). Ya existe, es local y no agrega dependencias.
- **Descartadas**: el llavero del sistema (`keyring` o Tauri), porque suma una dependencia nueva; el archivo `$HF_HOME/token`, porque vive en la carpeta de motores, que se mueve y se comparte entre worktrees.
- **Cómo revertir**: es una decisión de diseño. Para cifrarlo, mover la clave a un almacén del sistema y migrar el valor existente.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_credentials.py -q` (AC-4).
- **Pendiente**: decidir antes de `main` si el token debe cifrarse en reposo.

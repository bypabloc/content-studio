# 005: el job `tauri` de CI compila el crate de Tauri en Windows y corre también `cargo test`

- **Contexto**: el crate `client/src-tauri` no compila en ubuntu (no trae webkit2gtk), y `tauri::generate_context!()` exige `client/dist`. La prueba de regresión del Job Object de `server.rs` (D-2) usa `cmd`, `ping` y PowerShell, así que solo tiene sentido en Windows.
- **Elegida**: job `tauri` en `windows-latest`: `bun run --cwd client build`, luego `test-runner --type=tauri-check` (`cargo check`) y `cargo test --manifest-path client/src-tauri/Cargo.toml`. Caché de Rust con `Swatinem/rust-cache`.
- **Descartadas**: solo `cargo check` (la regresión del Job no llegaría a la CI); un job en ubuntu (no compila la app y el Job Object es de Windows); `cargo test --release` (más lento y el test no lo necesita).
- **Cómo revertir**: quitar el paso `cargo test` del job `tauri` en `.github/workflows/calidad.yml` (y la prueba de `server.rs` si se quita el Job Object).
- **Cómo comprobarla**: `cargo test --manifest-path client/src-tauri/Cargo.toml` en local (7 pruebas), y el job `tauri` verde en el PR con `gh pr checks <n> --watch`.
- **Límites**: `spawn` (CREATE_SUSPENDED en `server.rs`) no tiene prueba propia: la del Job crea su proceso suspendido, así que quitar el flag de `spawn` no la rompe. Lo cubre la verificación real de T9 (arrancar la app, cerrar la ventana y comprobar que el server muere). `is_alive` ya no cuenta un fallo de PowerShell como «muerto»: aborta la prueba.

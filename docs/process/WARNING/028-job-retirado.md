# 028: la ventana ya no posee el server: se retira el Job y sus dependencias

- **Contexto**: la ventana lanzaba `studio serve` dentro de un Job de Windows que lo mataba al cerrarse (`client/src-tauri/src/server/job.rs`). D-6 pide que el server sobreviva a la ventana, porque un MCP o un script puede estar usándolo.
- **Elegida**: la ventana se adjunta con `studio api up --with-token`, sin Job. Se borra `job.rs` y su test del nieto. Con ello dejan de usarse `windows` y `getrandom` (el token ya no se genera en Rust): se quitan de `Cargo.toml` y de la tabla de la regla.
- **Descartadas**: mantener el Job (mataría el server compartido al cerrar la ventana); conservar `job.rs` sin uso (código muerto, y su `dead_code` ensucia el build).
- **Cómo revertir**: restaurar `job.rs` desde el historial y volver a lanzar `serve` dentro del Job. Las dependencias `windows` y `getrandom` vuelven a `Cargo.toml`.
- **Cómo comprobarla**: `cargo test --manifest-path client/src-tauri/Cargo.toml`, y `python -m devtools test-runner --type=tauri-check`.

# 027: getrandom sube a 0.4.3 (salto de versión mayor)

- **Contexto**: la última estable de `getrandom` es 0.4.3; el crate lo fijaba en 0.3.4 (`=0.3.4`). Su único uso es `getrandom::fill` en `client/src-tauri/src/lib.rs:120`. Tauri 2.12.7 sigue con su propia 0.3.4, así que el árbol tiene dos versiones.
- **Elegida**: `=0.4.3`. `cargo test` (15 tests) y `tauri-check` pasan sin cambios en el código que usa `fill`.
- **Descartadas**: quedarse en 0.3.4 (contradice D-1, la última estable).
- **Cómo revertir**: `getrandom = "=0.3.4"` en `client/src-tauri/Cargo.toml` y `cargo update -p getrandom`.
- **Cómo comprobarla**: `cargo test --manifest-path client/src-tauri/Cargo.toml`.

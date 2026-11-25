# 028: cambiar el token detiene el server y la app se reconecta

- **Contexto**: el server valida el token que tenía al arrancar (`api/app.py`, `app.state.token`), así que rotarlo sin reiniciarlo no surte efecto. La fase 3 pedía el botón «Cambiar token» sin decir cómo, y su lista de archivos no incluía Rust.
- **Elegida**: el comando Tauri `rotate_token` hace `studio api down` (sin `--force`: con trabajos activos se niega y el token no cambia) y luego `studio api token --rotate`. El client llama a `api.reconnect()`, que vuelve a pedir `get_connection`: `api up --with-token` levanta el server con el token nuevo.
- **Descartadas**: un endpoint `POST /server/token/rotate` (duplica el apagado de `/server/stop` y habría que reimplementar la guarda de trabajos); rotar sin reiniciar (el server sigue con el token viejo); `--force` (cancelaría los trabajos del usuario).
- **Cómo revertir**: quitar `rotate_token` de `invoke_handler` en `client/src-tauri/src/lib.rs` y el botón del panel. `studio api token --rotate` sigue existiendo en la CLI.
- **Cómo comprobarla**: `cargo test --manifest-path client/src-tauri/Cargo.toml` (`rotate_*`) y `bun run --cwd client test` (`IntegrationsPanel`: confirmación, reconexión y fallo). En la verificación final: con un trabajo corriendo, cambiar el token se niega; sin trabajos, el token cambia y la app reconecta.

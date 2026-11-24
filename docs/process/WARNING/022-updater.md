# 022: el updater solo en la app instalada y su clave sin contraseña

- **Contexto**: con el updater activo en un checkout, `tauri dev` o `app-check` ofrecerían instalar el Release encima del entorno de desarrollo.
- **Elegida**: `lib.rs` registra `tauri-plugin-updater` solo en el modo instalado; en un checkout, «Buscar actualizaciones» dice que no pudo buscar. Instalar espera a que no haya trabajos corriendo; los encolados siguen tras reiniciar. El par de claves se generó sin contraseña en `~/.tauri/content-studio.key` (fuera del repo), así el secret de contraseña queda vacío.
- **Descartadas**: un flag de configuración para el modo (el modo ya lo detecta `bootstrap.rs`); pausar la cola antes de instalar (quedaría pausada tras reiniciar); una contraseña que nadie puede guardar en el lote.
- **Cómo revertir**: registrar el plugin siempre en `lib.rs`; generar otro par con contraseña y cambiar la `pubkey`.
- **Cómo comprobarla**: `bun run --cwd client test` (`useUpdater`, `AboutSettings`) y AC-9 con un `latest.json` local en la verificación final.
- **Pendiente**: antes del primer Release, el usuario carga los secrets `TAURI_SIGNING_PRIVATE_KEY` y `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` (`docs/operations/release.md`).

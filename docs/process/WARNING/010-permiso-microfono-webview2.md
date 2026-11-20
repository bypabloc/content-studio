# 010: el micrófono entra sin diálogo de permiso (WebView2 con `on_permission_request`)

- **Contexto**: la grabación pide el micrófono con `getUserMedia` dentro de la ventana de Tauri, que en Windows es WebView2. El usuario pidió que la app no muestre ningún permiso: el micrófono es lo que la app usa, y lo visible debe ser el indicador de uso (`010-micro-en-uso-y-registro`).
- **Elegida**: `tauri::Builder::on_permission_request` en `client/src-tauri/src/lib.rs` responde `Allow` solo a `PermissionKind::Microphone` y `Default` al resto. Tauri 2.12.7 lo pasa a `with_permission_handler` de wry 0.57, que en Windows usa el evento `PermissionRequested` de WebView2. No hace falta capability: Tauri no tiene un permiso de micrófono que añadir.
- **Descartadas**: una capability (no hay permiso de micrófono en Tauri); conceder todos los permisos (solo se concede el micrófono); seguir con el diálogo de WebView2.
- **Límite**: si Windows tiene apagado el acceso del micrófono para aplicaciones de escritorio (Configuración › Privacidad › Micrófono), WebView2 no puede abrirlo. La app lo muestra con el aviso de `voices.record.error`; esa opción no la cambia la app.
- **Cómo revertir**: quitar el bloque `.on_permission_request(...)` de `lib.rs`. WebView2 vuelve a preguntar.
- **Cómo comprobarla**: `cargo check` pasa. Falta la prueba real: abrir la app, grabar sin haber dado permiso antes y confirmar que no sale ningún aviso. PENDING `010-grabar-con-microfono-real`.

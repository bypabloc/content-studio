# 006: dependencia nueva: `@tauri-apps/plugin-dialog` (JS) para «Importar» con el diálogo del sistema

- **Contexto**: la spec pide «Importar» con `dialog.open`, que devuelve rutas en disco. El plugin de Rust (`tauri-plugin-dialog`, 2.8.4) ya estaba registrado y con `dialog:default` en las capabilities, pero faltaba su paquete de JS, que es el que llama al plugin desde la ventana.
- **Elegida**: `@tauri-apps/plugin-dialog` 2.8.4 exacto, igual que el crate. Las rutas van tal cual al server, que lee los guiones desde disco.
- **Descartadas**: `<input type="file">` (el WebView no entrega la ruta del archivo, y los trabajos la necesitan); un comando propio en Rust (duplica el plugin que ya está).
- **Cómo revertir**: quitar la dependencia de `client/package.json` y `bun.lock`, y `pick` de `useScriptImport`; «Importar» deja de existir.
- **Cómo comprobarla**: `bun run --cwd client test` (`useScriptImport.test.ts`) y, en la verificación final (T9), «Importar» abre el diálogo del sistema con el filtro de .txt y .json.

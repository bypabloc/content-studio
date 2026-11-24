# 005: plugins JS de Tauri para abrir la carpeta y la notificación de Windows

- **Contexto**: el toast de un trabajo terminado tiene «Abrir carpeta» (plugin opener) y, sin foco, sale una notificación de Windows (plugin notification). Los plugins de Rust ya están en `lib.rs` y sus permisos en `capabilities/default.json`; faltaba su parte JS.
- **Elegida**: `@tauri-apps/plugin-opener` 2.7.3 y `@tauri-apps/plugin-notification` 2.8.1, con versión exacta. Piden el permiso de notificación la primera vez (`requestPermission`).
- **Descartadas**: llamar a `explorer.exe` desde Rust (un comando nuevo solo para esto, y el permiso de shell); la notificación del navegador (`Notification`), que en WebView2 no sale como aviso de Windows.
- **Cómo revertir**: quitar los dos paquetes y el plugin de Rust correspondiente; `tauriAlerts` (`client/src/shared/notify/alerts.ts`) pierde «Abrir carpeta» y la notificación.
- **Cómo comprobarla**: `cd client && bun run test` (`alerts.test.ts` simula los plugins). Manual: con la ventana sin foco, al terminar un trabajo sale la notificación (T9).
- **Antes de**: el merge a `dev`.

# 024: el puerto de CDP se abre con la variable de WebView2, sin tocar Tauri

- **Contexto**: `app-check` necesita que la ventana de Tauri exponga CDP para que Playwright se conecte. La duda era si Tauri 2.12 respeta `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` o la pisa con sus argumentos por defecto.
- **Elegida**: la variable de entorno. El sondeo T1 (22-11-2026) abrió el binario de `tauri build --debug --no-bundle` con `--remote-debugging-port`. `/json/version` respondió (Edg/157), `/json/list` mostró la página `http://tauri.localhost/` y `connectOverCDP` leyó los 11 enlaces de la barra y sacó una captura.
- **Descartadas**: leer `CONTENT_STUDIO_CDP_PORT` en `lib.rs` con `additional_browser_args` (cambia el producto sin necesidad); `tauri-driver` (dos binarios más).
- **Cómo revertir**: quitar la variable del entorno que arma `devtools/app_check/env.py`.
- **Cómo comprobarla**: `python -m devtools app-check run` sale con 0 y `report.json` trae las capturas.

# 031: el desinstalador deja la carpeta de instalación vacía

- **Qué**: tras `uninstall.exe /S` los archivos se van, los accesos de «Enviar a» y el valor `Run` también, pero queda vacío el directorio de instalación (`Content Studio`).
- **Por qué queda así**: el borrado final del directorio lo hace el desinstalador de Tauri; no bloquea nada del usuario.
- **Cómo cerrarlo**: revisar si el directorio se borra al terminar el desinstalador (o con `RMDir $INSTDIR` en `hooks.nsh`) y comprobarlo con `app-check` tras desinstalar.
- **Cuándo**: después de publicar 031.

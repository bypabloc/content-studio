# 022: borrar los datos al desinstalar con la casilla de Tauri

- **Contexto**: D-5 pedía una casilla propia en `NSIS_HOOK_PREUNINSTALL` y textos en `installer/nsis/strings-es.nsh`. El desinstalador de Tauri 2 ya trae la casilla «Borrar los datos de la aplicación» (desmarcada) y su texto en español.
- **Elegida**: usar esa casilla. `installer/nsis/hooks.nsh` (`NSIS_HOOK_POSTUNINSTALL`), si está marcada y no es una actualización, pide una confirmación más y borra `%LOCALAPPDATA%\Content Studio` y `Documentos\Content Studio`; con `CONTENT_STUDIO_HOME` (una instalación aislada), solo esa carpeta, igual que la app guarda ahí también las salidas (`paths.outputs_dir`). Siempre borra `$INSTDIR\app` (el server corre ahí como instalación editable y Python deja sus `__pycache__`, que el desinstalador no conoce). Sin `strings-es.nsh`: el único texto propio es el de la confirmación.
- **Descartadas**: una página propia con nsDialogs (duplica la casilla de Tauri, que borraría solo la carpeta del identificador); borrar sin confirmar.
- **Cómo revertir**: quitar `installerHooks` de `tauri.conf.json` y el archivo.
- **Cómo comprobarla**: AC-8 en la verificación final (desinstalar con y sin la casilla).
- **Pendiente**: ninguno.

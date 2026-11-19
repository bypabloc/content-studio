# 005: «Abrir carpeta» de los avisos necesita el permiso `opener:allow-open-path`

- **Contexto**: el aviso de un trabajo terminado trae la acción «Abrir carpeta», que llama a `openPath` del plugin opener. Con solo `opener:default` la llamada falla por permisos. El permiso `allow-open-path` está documentado como «sin ningún alcance preconfigurado»: la webview podría abrir cualquier ruta.
- **Elegida**: `opener:allow-open-path` en `client/src-tauri/capabilities/default.json`. La ventana es local y las rutas que pide la app salen de los trabajos del server (carpetas `out/`).
- **Descartadas**: no agregar la acción (pierde el aviso útil); un alcance con `$DOCUMENT/**` (las salidas viven en la carpeta del proyecto o, con la 015, en la carpeta de datos del usuario, y el alcance tendría que cambiar con cada una).
- **Cómo revertir**: quitar `"opener:allow-open-path"` de `default.json`. La acción «Abrir carpeta» dejará de funcionar.
- **Cómo comprobarla**: en la app real, un trabajo terminado con «Abrir carpeta» abre la carpeta de salida. Antes del merge a `main` hay que decidir el alcance cuando la 015 fije la carpeta de datos.

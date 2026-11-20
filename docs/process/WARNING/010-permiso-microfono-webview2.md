# 010: el permiso del micrófono en WebView2 no se ha probado con un micrófono real

- **Contexto**: la grabación pide el micrófono con `getUserMedia` dentro de la ventana de Tauri, que en Windows es WebView2. La capability de la ventana (`client/src-tauri/capabilities/default.json`) no incluye ningún permiso de micrófono: sus permisos son `core:default`, el diálogo, abrir, notificaciones y el estado de la ventana.
- **Elegida**: no añadir permisos de Tauri, porque no hay un permiso de micrófono que añadir. Lo que WebView2 haga en el primer `getUserMedia` (pedir permiso, concederlo o negarlo) no se comprobó y queda para la prueba real.
- **Descartadas**: añadir una capability a ciegas, sin saber cómo responde WebView2.
- **Cómo revertir**: no aplica hasta la prueba real.
- **Cómo comprobarla**: PENDING `010-grabar-con-microfono-real`. Abrir la app, grabar una toma y anotar qué pidió WebView2, y qué pasó al negar el permiso.

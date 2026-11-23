# 018: app-check no obtiene CDP

- **Qué**: Tres corridas de `python -m devtools app-check run --data=temp` compilaron el binario Tauri, pero WebView2 no respondió en el puerto CDP.
- **Por qué no se hizo**: el proceso de la app no expuso DevTools Protocol antes del timeout de 60 s; los logs no muestran una excepción de la app.
- **Cuándo**: repetir cuando una corrida de app-check consiga abrir la ventana y responder a CDP.
- **Quién**: agente.
- **Qué la cierra**: `app-check run --data=temp` termina el escenario smoke y entrega su resultado final.

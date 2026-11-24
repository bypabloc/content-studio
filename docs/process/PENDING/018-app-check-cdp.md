# 018: app-check no obtiene CDP

- **Qué**: Cuatro corridas compilaron Tauri, pero WebView2 no respondió en el puerto CDP; la cuarta fue en la spec 019.
- **Por qué no se hizo**: el proceso de la app no expuso DevTools Protocol antes del timeout de 60 s; los logs no muestran una excepción de la app.
- **Cuándo**: repetir cuando una corrida de app-check consiga abrir la ventana y responder a CDP.
- **Quién**: agente.
- **Qué la cierra**: `app-check run --data=temp` termina el escenario smoke y entrega su resultado final.

## Repetición en 019

- Tauri compiló en `tmp/app-check/20261123-222528` con datos temporales.
- WebView2 rechazó CDP en `127.0.0.1:13400`; los dos escenarios smoke fallaron y no tomaron capturas.
- Log: `logs/app-check-20261123-222528.log`.

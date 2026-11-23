# 017: falta verificar el flujo completo en la ventana de Tauri

- **Qué**: `app-check --data=temp` compiló la app tres veces, pero no obtuvo respuesta de CDP en los puertos 65012, 53328 y 47160. El CLI real y los e2e de Playwright sí se ejecutaron; faltan las capturas y las acciones de la ventana real.
- **Por qué no se hizo**: `app-check` no logró conectar Playwright a WebView2; Computer Use está prohibido por las reglas del repo.
- **Cuándo**: cuando CDP responda desde `python -m devtools app-check run`; completar la grabación física de 10 s, arrastrar desde Windows, la segunda toma con auriculares, palmada de latencia y capturas en claro/oscuro.
- **Quién**: agente.
- **Qué la cierra**: `report.json` y capturas de app-check en verde, más medición de desfase <20 ms con micrófono y auriculares físicos, o un motivo medido en `017-latencia-grabacion.md`.
- **Impacto**: no bloquea el merge a `dev`; T8 automatiza importar, dividir, exportar, deshacer/rehacer, marcadores y reasignar fuentes.

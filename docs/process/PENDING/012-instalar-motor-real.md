# 012: cerrar la aceptación manual de la spec

- **Qué**: completar AC-10 desde Motores: interrumpir o cancelar la descarga, reanudar, verificar, reparar sin volver a bajar pesos y desinstalar; capturar Motores, Almacenamiento y Bienvenida en claro y oscuro.
- **Verificado por CLI**: job 2 instaló Qwen 0.6B en almacenamiento temporal (7,622,684,386 B; descarga HF 2,516,106,051 B); job 4 verificó 1.000 s (-18.27 LUFS, -1.50 dBTP); job 10 reparó sin volver a descargar pesos; job 11 desinstaló Qwen y limpió el almacenamiento temporal. El venv externo conservó ruta y fecha.
- **Pendiente en UI**: probar ffmpeg ausente, el banner y winget; mover 2 o 3 salidas creadas por la spec entre discos, comparar SHA-256 y `/files`, y volverlas a mover; recorrer Bienvenida con datos temporales y el paquete pesado desmarcado. Si no hay segundo disco, registrarlo.
- **Por qué falta**: CUA no conectó para operar la app ni capturar sus pantallas; el CLI no comprueba la UI.
- **Cuándo**: después del merge a `dev`; no bloquea la fusión. La bienvenida y la desinstalación de la UI ya tienen e2e (`tests/e2e/welcome`, `tests/e2e/engines`); ver `WARNING/012-aceptacion-sin-usuario.md`.
- **Quién**: usuario.
- **Qué la cierra**: completar las comprobaciones UI, registrar winget y traslado en WARNING, revisar las capturas en claro y oscuro, y confirmar de nuevo el venv externo intacto.

# 012: validar la instalación de motores desde la app

- **Qué**: completar el flujo de instalación, verificación, reparación y desinstalación de Qwen desde la app; revisar las pantallas en claro y oscuro.
- **Verificado por CLI**: job 2 instaló Qwen 0.6B en almacenamiento temporal (7,622,684,386 B; descarga HF 2,516,106,051 B); job 4 verificó 1.000 s (-18.27 LUFS, -1.50 dBTP); job 10 reparó sin volver a descargar pesos; job 11 desinstaló Qwen y limpió el almacenamiento temporal. El venv externo conservó ruta y fecha.
- **Por qué falta**: CUA no conectó para operar la app ni capturar sus pantallas.
- **Cuándo**: T9, antes de fusionar la spec 012.
- **Quién**: usuario y agente.
- **Qué la cierra**: operar el flujo desde la app, revisar las capturas en claro y oscuro, y volver a confirmar el venv externo intacto.

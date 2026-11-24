# 012: la prueba TTS usa una voz de catálogo con consentimiento

- **Contexto**: la ruta `server/data/narration/reference/test/` de la spec no existe. El catálogo confirma que `yesid` tiene licencia CC0-1.0 y consentimiento para clonación.
- **Elegida**: usar `yesid` para la frase breve de la prueba de humo. La prueba local solo corre cuando se selecciona `CONTENT_STUDIO_VERIFY_ENGINE`.
- **Descartadas**: usar perfiles privados del checkout o cargar todos los motores durante las pruebas generales podría leer datos personales o tomar la GPU sin una selección explícita.
- **Cómo revertir**: revierte el commit T6 y cambia la prueba al fixture versionado que sustituya `reference/test/`; no muevas ni borres perfiles existentes.
- **Cómo comprobarla**: las pruebas unitarias verifican que TTS envía `--voice yesid`; la prueba local requiere seleccionar un motor y tomar el candado de GPU.
- **Pendiente**: [012-instalar-motor-real](../PENDING/012-instalar-motor-real.md), AC-10 en T9.

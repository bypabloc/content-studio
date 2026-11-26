# Antes de difundir el instalador: firma de código y revisión de en/pt

- **Contexto**: las versiones se publican sin firma de código, así que SmartScreen muestra «Windows protegió tu PC». Además, las traducciones al inglés y al portugués las escribió el agente, y la etapa `i18n` solo comprueba claves y parámetros. Los secrets del updater ya están cargados, y la v0.1.0 y la v0.2.0 se publicaron.
- **Elegida**: publicar sin firma para el círculo de prueba hasta que el usuario decida.
- **Descartadas**: contratar una firma sin el usuario, porque tiene costo. Las opciones son Azure Trusted Signing (unos 10 USD al mes), un certificado OV (unos 200 a 400 USD al año) o uno EV (unos 300 a 600 USD al año, con reputación inmediata).
- **Cómo revertir**: no aplica.
- **Cómo comprobarla**:
  - Firma: un Release cuyo instalador no muestre el aviso en un Windows limpio. El agente agrega el paso de firma a `release.yml`.
  - Traducciones: una persona lee `server/src/content_studio/messages/en.json` y `pt.json`.

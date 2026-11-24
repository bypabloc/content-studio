# 022: firmar el instalador para que SmartScreen no lo frene

- **Qué**: el instalador sale sin firma de código: Windows muestra «Windows protegió tu PC» hasta que el archivo gana reputación. Opciones: Azure Trusted Signing (unos 10 USD al mes, exige identidad verificada y una cuenta de Azure), un certificado OV (unos 200 a 400 USD al año; la reputación se gana con el tiempo) o uno EV (unos 300 a 600 USD al año, con token físico o HSM en la nube; la reputación es inmediata).
- **Por qué no se hizo**: tiene costo (spec 022, D-8); la decisión es del usuario.
- **Cuándo**: antes de difundir el instalador fuera del círculo de prueba.
- **Quién**: usuario (elige y contrata); agente (agrega el paso de firma a `release.yml`).
- **Qué la cierra**: un Release cuyo instalador no muestra el aviso en un Windows limpio.

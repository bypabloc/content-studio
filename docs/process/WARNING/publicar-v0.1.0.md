# Publicar la v0.1.0: lo que solo puede hacer el usuario

- **Contexto**: `dev` está lista para un PR a `main`, pero el agente no abre ese PR sin un pedido explícito (`git-workflow.md`). El instalador se compila, pero el updater no se firma sin la clave privada.
- **Elegida**: dejar el PR `dev → main` sin abrir hasta que el usuario lo pida. Antes del primer tag hay que hacer esto:
  1. Cargar los secrets `TAURI_SIGNING_PRIVATE_KEY` y `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` en GitHub (`docs/operations/release.md`). Sin ellos, `tauri build` falla con «A public key has been found, but no private key».
  2. Decidir la firma de código del instalador. Sin firma, SmartScreen muestra «Windows protegió tu PC». Las opciones son Azure Trusted Signing (unos 10 USD al mes), un certificado OV (unos 200 a 400 USD al año) o uno EV (unos 300 a 600 USD al año, con reputación inmediata). También se puede publicar sin firma para el círculo de prueba.
  3. Que una persona lea `server/src/content_studio/messages/en.json` y `pt.json`. Los tradujo el agente, y la etapa `i18n` solo comprueba claves y parámetros.
  4. Pedir el PR `dev → main` y el tag. Después, el agente corre `gh workflow run release.yml -f tag=v9.9.9 -f dry-run=true`, que solo se puede lanzar con el workflow ya en `main`.
- **Descartadas**: publicar sin la clave del updater, porque la app instalada no podría actualizarse.
- **Cómo revertir**: no aplica.
- **Cómo comprobarla**: un Release con el instalador, su firma y `latest.json`.

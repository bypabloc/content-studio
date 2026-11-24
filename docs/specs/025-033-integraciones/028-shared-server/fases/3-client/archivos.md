# Spec 028, fase 3: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## client/src/

### Modificar

- `client/src/shared/api/client.ts`, `events.ts` — reconexión.
- `client/src/features/settings/` — `IntegrationsPanel.tsx` nuevo y su línea en la pantalla de Ajustes.
- `server/src/content_studio/messages/{es,en,pt}.json` — claves de 02 §5.
  - Verify: `bun run --cwd client test && python -m devtools test-runner --type=i18n`

### Crear

- Tests espejo en `client/tests/unit/src/` y los e2e de la fase.

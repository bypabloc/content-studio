# Spec 026, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## server/src/content_studio/engines/

### Modificar

- `server/src/content_studio/engines/installer.py` — guarda la huella al terminar.
- `server/src/content_studio/engines/verification.py` — estado `outdated`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/engines -q`
- `server/src/content_studio/api/routes/engines.py` y `api/schemas.py` — el estado nuevo.

## client/

### Modificar

- `client/src/features/engines/` (la tarjeta del motor) — aviso y botón.
- `server/src/content_studio/messages/{es,en,pt}.json` — `engines.outdated`, `action.update`.
  - Verify: `python -m devtools test-runner --type=i18n`
- `client/src/shared/api/schema.d.ts` — `bun run --cwd client gen:api`.

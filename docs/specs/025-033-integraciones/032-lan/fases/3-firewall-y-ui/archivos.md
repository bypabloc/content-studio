# Spec 032, fase 3: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## client/

### Crear

- `client/src-tauri/src/firewall.rs`.
- `client/src/features/settings/LanPanel.tsx` y su test; los e2e.
- `docs/operations/lan.md` — emparejar, huella, límites y Tailscale Serve para fuera de casa.

### Modificar

- `client/src-tauri/Cargo.toml` — feature `Win32_UI_Shell` de `windows`.
- `client/src/features/settings/IntegrationsPanel.tsx`.
- `server/src/content_studio/messages/{es,en,pt}.json` — `settings.lan.*`.
  - Verify: `python -m devtools test-runner --type=tauri-check && bun run --cwd client test`

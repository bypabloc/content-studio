# Spec 027, fase 3: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## Reglas

### Modificar

- `.agents/rules/frontend-stack.md` y su copia de `.claude/` (`rules --sync`) — tabla «Versiones».
  - Verify: `python -m devtools rules && python -m devtools agent-context`
- `tests/validators/test_pins.py` — el caso de la tabla.

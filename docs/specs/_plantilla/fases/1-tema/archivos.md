# Spec <NN>, fase 1: archivos

Rutas desde la raíz, agrupadas por módulo. Cada archivo con su verificación; cada `.py` de fuente queda en 300 líneas o menos (`codigo-python.md`).

## <server/src/content_studio/<módulo>/>

### Crear

- `<ruta>` — <qué contiene>.
  - Verify: `uv run pytest <test> -q`

### Modificar

- `<ruta>` — <qué cambia>.
  - Verify: `<comando>`

### Eliminar

- `<ruta>` — <por qué>.

### Solo lectura

- `<ruta>` — <patrón a seguir o dependencia>.

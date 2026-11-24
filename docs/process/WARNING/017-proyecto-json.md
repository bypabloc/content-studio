# 017: el proyecto se guarda como JSON versionado en su carpeta

- **Contexto**: la línea de tiempo debe abrirse y guardarse como un proyecto portable, sin añadir binarios ni tablas específicas a SQLite.
- **Elegida**: esquema `version: 1` en `project.json`, junto a `media/` y `exports/`; la API valida el documento y usa hash `If-Match` para evitar sobrescrituras concurrentes.
- **Descartadas**:
  - Guardar clips o medios binarios en SQLite: incumple la regla de metadatos y dificulta mover el proyecto.
  - Convertir silenciosamente una versión futura: podría perder operaciones nuevas sin avisar.
- **Cómo revertir**: migrar el esquema en `editor/project.py` y `editor/store.py`, conservando la lectura de v1 hasta completar los proyectos existentes.
- **Cómo comprobarla**: `server/tests/unit/src/content_studio/editor/` y las pruebas de concurrencia de `api/routes/test_editor.py`.
- **Pendiente**: definir una migración explícita cuando exista un esquema posterior a v1.

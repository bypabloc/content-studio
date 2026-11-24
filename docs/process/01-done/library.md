---
modulo: library
actualizada: 2026-11-24
---

# Biblioteca

## Qué resuelve

Un solo lugar para lo que genera el estudio y lo que hay en las carpetas que el usuario agrega: buscar, filtrar, etiquetar, agrupar en proyectos, reproducir, ver el origen y repetir, mandar a otra sección, renombrar, mover, mandar a la papelera y ver qué ocupa espacio.

## Qué hace hoy

- Índice en SQLite (migración 7): solo rutas, tamaños, fechas, duración y etiquetas; nunca contenido. El worker registra las salidas de cada trabajo `done`; los anteriores se indexan una vez al abrir la base.
- Carpetas vigiladas: `library.scan` (CPU) agrega, actualiza y marca faltantes sin borrar registros; corre al abrir la Biblioteca si el último escaneo tiene más de 5 minutos, y con «Actualizar».
- Búsqueda por nombre y etiquetas; «Buscar también en el contenido» lee de disco los `script.json` y las transcripciones. Filtros por tipo, medio, fecha, duración, etiqueta, proyecto, carpeta y ★.
- Detalle con reproductor, metadatos, parámetros del trabajo, «Repetir», «Editar y repetir» (`?from_job=` en Narración, Música, Limpiador, Subtítulos, Convertir y Mezcla) y «Mandar a…».
- Renombrar y mover nunca sobrescriben (`path_exists`); borrar manda a la papelera de Windows (`send2trash`); referencias, voces y motores están protegidos (`protected_path`).
- Espacio: barras por tipo, lo más pesado y las tomas no elegidas, con papelera en lote y una sola confirmación.
- Miniaturas de video en `<datos>/cache/thumbs/`; la onda del audio se dibuja con `/media/peaks`.
- CLI: `uv run studio library list|scan|tag|trash`.

## Dónde vive

- Server: `server/src/content_studio/library/` (index, scan, thumbs, query, text_search, tags, projects, actions, storage), `api/routes/library*.py`, `services/library_scan.py` y `cli/library.py`.
- Cliente: `client/src/features/library/`, `shared/hooks/useFromJob.ts` y `shared/components/molecules/UIVirtualList/`.
- Pruebas: `server/tests/unit/src/content_studio/library/`, `client/tests/unit/src/features/library/` y `tests/e2e/library/`.
- Decisiones: [020-indice-inicial](../WARNING/020-indice-inicial.md), [020-busqueda-en-disco](../WARNING/020-busqueda-en-disco.md), [020-send2trash](../WARNING/020-send2trash.md) y [020-editar-y-repetir](../WARNING/020-editar-y-repetir.md).

## Historial

- 2026-11-24: spec 020, Biblioteca de medios.

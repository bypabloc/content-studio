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
- Las carpetas de entrada (spec 030) no son carpetas vigiladas: no indexan nada en la biblioteca. Lo que se suelta en
  una carpeta de entrada se procesa y su resultado queda en su `done/`, no aquí.

## Dónde vive

- Server: `server/src/content_studio/library/` (index, scan, thumbs, query, text_search, tags, projects, actions, storage), `api/routes/library*.py`, `services/library_scan.py` y `cli/library.py`.
- Cliente: `client/src/features/library/`, `shared/hooks/useFromJob.ts` y `shared/components/molecules/UIVirtualList/`.
- Pruebas: `server/tests/unit/src/content_studio/library/`, `client/tests/unit/src/features/library/` y `tests/e2e/library/`.
- Decisiones (historial de git de `docs/process/WARNING/`): 020-indice-inicial, 020-busqueda-en-disco, 020-send2trash y 020-editar-y-repetir.

## Verificación (2026-11-24)

- Batería: `test-runner --type=all` (pytest 1944; `client-unit` con cobertura), `e2e` (exit 0), `budget`, `guard-tdd` y `-m local` (papelera real) pasan.
- `app-check run` (smoke): exit 0, 26 capturas en claro y oscuro, también de la Biblioteca.
- CLI: `studio library trash` sobre una referencia sale con 1 y `protected_path`; el archivo queda.
- Real: `out/` del principal como carpeta vigilada, en solo lectura: 293 medios en 13 s, con duración en audio y video.
- Espacio: el total de la carpeta coincide con `du -sb` (762 774 647 B); lo indexado suma 734 585 369 B (el resto no son medios).
- `tmp/spec-020/videos`: 3 medios, uno borrado a mano queda faltante; renombrar, mover y papelera real sobre esos archivos.
- Las salidas reales no tienen `script.json`: la búsqueda en el contenido se verificó con las pruebas de `text_search`.

## Historial

- 2026-11-24: «Publicar» en el detalle: títulos, descripción, hashtags y capítulos por plataforma (spec 021).
- 2026-11-24: spec 020, Biblioteca de medios.
- 2026-11-24: verificación integral (023): las exportaciones del Editor se indexan desde su `result.json`.

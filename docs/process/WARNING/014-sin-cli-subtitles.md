# 014: sin subcomando `studio subtitles` (ciclo 8)

**Qué se decidió.** La CLI no tiene `studio subtitles`. Ningún criterio de aceptación ni decisión de la spec lo pide, y la API y la UI cubren el flujo completo: crear, editar, exportar, quemar y traducir. El punto 3 de la batería de `03-verificacion-final.md` queda sin efecto.

**Cómo revertirla.** Añadir un subcomando en `cli/main.py` que llame a los mismos servicios que la API (`services/subtitles_*`), como hace `narration`.

**Dónde.** `server/src/content_studio/cli/main.py` (sin cambios para subtítulos).

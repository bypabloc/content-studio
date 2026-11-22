# 014: fuentes incluidas (OFL) y listado

**Qué se decidió (ciclo 4, AC-8).**

- **Binarios en el repo: 2,7 MB** en `server/data/fonts/`, excepción a «sin binarios» de D-6: 12 TTF y un `OFL.txt` por familia. Ninguna de las cinco OFL declara un Reserved Font Name, así que las instancias pueden llevar el nombre de familia.
- **Origen**: `google/fonts` (rama `main`, 21/11/2026). Poppins y Bebas Neue son estáticas y van tal cual. Montserrat, Inter e Inter Tight solo tienen variables en ese repo: las estáticas se generaron con fontTools (herramienta de desarrollo, no dependencia de la app):
  `python -m fontTools.varLib.instancer --static --update-name-table <variable> wght=<peso>` (Inter con `opsz=14`).
  Pesos: Montserrat 400, 700 y 800 (ExtraBold lo usa el preset `reels`); Inter 400 y 700; Inter Tight 400 y 700.
- **Familia = nameID 16 (o 1) y estilo = nameID 17 (o 2).** Así `Montserrat ExtraBold` es el estilo ExtraBold de Montserrat y la familia visible son las 5 de AC-8. El preset `reels` guarda el `Fontname` «Montserrat ExtraBold» (nameID 1 del archivo): comprobar en el ciclo de quemado (ciclo 5) que libass lo resuelve.
- **Forma de la respuesta**: una entrada por familia, con `path` = su archivo Regular (o el primero) y `styles` ordenados. JASSUB necesita los demás estilos: se decide en el client (T7).
- **Sin caché.** D-6 la pedía; el listado real tardó 28 ms con 327 archivos del sistema, así que no se implementa.
- **`/files`** sirve las carpetas enteras de fuentes (`server/data/fonts` y, en Windows, `%WINDIR%\Fonts` y `%LOCALAPPDATA%\Microsoft\Windows\Fonts`), no solo las listadas. Es lectura, bajo el token de la API.
- **Limitaciones**: los `.ttc` no se listan. En POSIX se usa `fc-list --format=%{file}\n`; la prueba lo simula, no se ha ejecutado en Linux.

**Dónde.** `subtitles/fonts.py`, `api/routes/subtitles.py` (`GET /subtitles/fonts`, declarada antes de `/subtitles/{project_id}`), `api/app.py` (raíces de `/files`), `server/data/fonts/`.

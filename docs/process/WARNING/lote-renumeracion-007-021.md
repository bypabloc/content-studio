# Lote 001-017-studio: renumeraciones de la 007 en adelante y carpeta con su nombre viejo

- **Contexto**: el 2026-11-19 el usuario sumó tres veces specs nuevas en medio del lote y pidió que el número siga el orden de ejecución, sin tocar la 006, que otra sesión estaba ejecutando.
  1. Iconos (justo después de la 006) y el Editor (después de la mezcla, antes de la Biblioteca).
  2. i18n (catálogo único de textos en es, en y pt), justo después de la 006, para que cada spec siguiente traiga sus textos en los tres idiomas.
  3. Componentes con Atomic Design traídos de klinikae, con bloqueo de etiquetas HTML nativas fuera de los átomos, justo después de la i18n. La spec de iconos se recortó, porque la 008 trae `UIIcon`, `UIIconButton`, `UITooltip` y la sidebar colapsable.
- **Elegida**:
  - **Primera renumeración**: 007 iconos (nueva), 008 voces (era 007), 009 música (008), 010 motores (009), 011 limpiador (010), 012 subtítulos (011), 013 convertir (012), 014 mezcla (013), 015–017 editor (nuevas), 018 biblioteca (014), 019 LLM (017), 020 instalador (015) y 021 verificación integral (016).
  - **Segunda**: 007 i18n (nueva), y de la 007 a la 021 todas suben uno.
  - **Tercera**: 008 componentes (nueva), y de la 008 a la 022 todas suben uno.
  - **Estado final**:
    - 007 i18n y 008 componentes;
    - 009 iconos, 010 voces, 011 música, 012 motores, 013 limpiador, 014 subtítulos, 015 convertir y 016 mezcla;
    - 017–019 editor, 020 biblioteca, 021 LLM, 022 instalador y 023 verificación integral.
  - En las tres, la carpeta del lote conserva el nombre `001-017-studio` y la 006 no cambia. Así, el cierre de la 006 (que borra su carpeta y edita el README del lote) no choca con un renombre de carpeta.
  - La segunda y la tercera tampoco editan la 003 ni la 006, que están en ejecución. Sus menciones a otros números quedan viejas y se borran con sus carpetas al cerrarlas.
  - En `docs/process/`, cspell y las reglas se actualizaron las menciones a voces (`grabar/`, ahora 010), música (011) e instalador (022). `docs/research/` no se tocó: sus números citan la spec del momento en que se escribió.
  - En las specs 010–023, los componentes compartidos pasaron a su nivel y prefijo (`molecules/UIJobPicker/`, `UIIcon name="magnet"`, `UIIconButton`).
- **Descartadas**: renumerar también la 006 (rompía su rama y su worktree en ejecución); renombrar la carpeta a `001-023-studio` (conflicto rename/delete con el cierre de la 006); dejar los números viejos con las nuevas al final (el usuario pidió que el número siga el orden).
- **Cómo revertir**: revertir el commit `docs: specs 007 (iconos) y 015-017 (editor NLE)…` de la rama `docs/specs-editor-iconos` y los commits de la rama `docs/spec-007-i18n`.
- **Cómo comprobarla**: `ls docs/specs/001-017-studio/` muestra 003, 006 y de la 007 a la 023 en orden, y `grep -rn "0[012][0-9]-" docs/specs/README.md` coincide con las carpetas. La 023 borra la carpeta del lote y esta ficha.

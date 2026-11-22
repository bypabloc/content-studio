# 014: escucha y revisión de los subtítulos

- **Qué**: escuchar la narración alineada y comprobar que los cues coinciden con el audio (sincronía); revisar el editor y la vista previa en la app real, en claro y en oscuro; abrir el SRT, el VTT y el ASS en un editor externo; y decidir si los presets incluidos (`styles.py`: tamaños, colores, pop) se quedan como están.
- **Por qué no se hizo**: el gusto y la sincronía percibida los decide el usuario (plan 03, §3). El agente no puede escuchar.
- **Cuándo**: después del merge a `dev`; no bloquea. Si pide ajustes de gusto, se hacen en una spec posterior, porque son datos de `styles.py`.
- **Quién**: usuario.
- **Qué la cierra**: el usuario confirma los presets y la sincronía, o pide cambios que se aplican en una spec propia.

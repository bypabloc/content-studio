# 019: control de velocidad en el Inspector

- **Contexto**: AC-4 permite cambiar la velocidad de clips de audio y video, pero el Inspector solo editaba clips visuales.
- **Elegida**: agregar un campo numérico de 0,25× a 4× para audio y video; persistirlo y sincronizar clips enlazados.
- **Alcance**: el control aparece en el Inspector existente; imagen y título conservan su duración base.
- **Descartadas**: dejar la velocidad solo en el JSON del proyecto o crear un panel aparte para un único control.
- **Cómo revertir**: revertir el commit T3 y quitar esta ficha de los índices de 019 y WARNING.
- **Pruebas espejo**: el test-runner exige que cada test file tenga su módulo fuente; los casos AC-4 viven junto a sus renderers.
- **Cómo comprobarla**: `Inspector.test.tsx`, `EditorVisualPanel.test.tsx`, pruebas de playback y render FFmpeg AC-4.
- **Pendiente**: ninguna.

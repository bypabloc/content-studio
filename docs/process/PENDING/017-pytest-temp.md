# 017: dos carpetas temporales de pytest quedaron en la raíz del worktree

- **Qué**: `Userspacg1projectsbypabloccontent-studio-worktrees017-editor-coretmptest-runnerpytest-basetemp-probe/` y `Userspacg1projectsbypabloccontent-studio-worktrees017-editor-coretmptest-unit-full/` son temporales generados por corridas de prueba anteriores.
- **Por qué no se limpió**: Synapse bloqueó el borrado recursivo fuera de `./tmp/` y exige aprobación manual. No se intentó otro comando.
- **Cuándo**: después de que el usuario apruebe la ejecución puntual indicada por Synapse, antes de quitar el worktree.
- **Quién**: usuario.
- **Qué la cierra**: borrar solo esas dos rutas, tras verificar que están dentro de `017-editor-core`, y confirmar `git status --short` limpio.
- **Impacto**: datos temporales de pytest; no afectan los artefactos del Editor ni los otros worktrees.

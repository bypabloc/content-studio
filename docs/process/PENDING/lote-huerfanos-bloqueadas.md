# Lote 001-017: 12 carpetas huérfanas y temporales

- **Qué**: quedan 11 carpetas huérfanas en `content-studio-worktrees/` y un temporal de pytest accidental en `019-editor-effects`.
- **Por qué falta**: ocho carpetas de pytest tienen ACL de administrador; procesos retienen las de 015 y 018; Synapse exige aprobación manual para borrar las carpetas fuera de `tmp`.
- **Temporal 019**: `D:\Users\pacg1\projects\bypabloc\content-studio-worktrees\019-editor-effects\Userspacg1projectsbypabloccontent-studio-worktreesp019-text-route-5647b814a1ce4db0b74b521b91e57d95` se creó por una ruta `--basetemp` mal escapada; se verificó que está dentro del worktree y no es un enlace.
- **Aprobación manual**: Synapse bloqueó su borrado recursivo, evento `3f98ee0f`. El usuario puede autorizarlo en su terminal con `python "C:\Users\pacg1\.codex\plugins\cache\bypabloc-agents\synapse\1.7.4\scripts\synapse.py" approve 3f98ee0f`.
- **Cuándo**: cuando el usuario lo autorice en su terminal; no bloquea las specs del lote.
- **Quién**: usuario.
- **Qué la cierra**: borrar las carpetas huérfanas; no tocar datos de usuario ni worktrees registrados.

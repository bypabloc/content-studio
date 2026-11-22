# 024: `app-check` compila en un target propio del worktree

- **Contexto**: `worktree prepare` enlaza `client/src-tauri/target` al target compartido `<principal>/tmp/cargo-target`. `project_root()` de `client/src-tauri/src/lib.rs` se fija al compilar (`env!("CARGO_MANIFEST_DIR")`), así que un binario de ese target abre el server del último checkout que compiló. En el lote 012, Codex probó un binario anterior al commit bajo prueba.
- **Elegida**: `app-check` compila con `tauri build --debug --no-bundle` y `CARGO_TARGET_DIR=<worktree>/tmp/app-check/cargo-target`. El frontend queda embebido, sin Vite ni el puerto 1420. El informe trae `commit` y `binary`. La primera compilación tarda minutos y las siguientes son incrementales (unos 10 s con un cambio chico, medido el 22-11-2026).
- **Descartadas**: el target compartido (otro checkout); `tauri dev` (Vite en 1420 choca entre sesiones, y el binario espera ese servidor); cambiar `worktree prepare` (el target compartido sigue sirviendo para `tauri-check`).
- **Cómo revertir**: cambiar `CARGO_TARGET_DIR` en `devtools/app_check/env.py`.
- **Cómo comprobarla**: `python -m devtools app-check run`: `commit` del informe igual a `git rev-parse HEAD`. Si el binario de la corrida anterior sigue abierto, la compilación sale con exit 2 y el mensaje «content-studio.exe of this worktree is still open».

# 031: inicio con Windows con un valor Run de HKCU

- **Contexto**: AC-8 pide que el server arranque al iniciar sesión, sin admin y apagado por defecto (D-4).
- **Elegida**: el valor `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\ContentStudioServer` = `"<venv>\Scripts\pythonw.exe" -m content_studio api up`, escrito con `RegSetKeyValueW` y borrado con `RegDeleteKeyValueW` de la crate `windows` =0.62.2. El venv es el de la app instalada (`%LOCALAPPDATA%\Content Studio\venv`); en el checkout el comando responde error y no toca el registro al apagarlo.
- **Descartadas**: una tarea programada (pide permisos y aparece en el programador de tareas); la carpeta Inicio (un acceso directo que se rompe si cambia la ruta); la crate `winreg` (la API de `windows` ya está en el árbol); un servicio de Windows (pide admin).
- **Cómo revertir**: quitar `StartAtLogin.tsx` y su fila en `SettingsPage.tsx`, el comando `set_start_at_login` de `lib.rs`, `startup.rs`, `installed_venv` de `bootstrap.rs` y la crate `windows`. Antes, apagar el interruptor (o borrar el valor `ContentStudioServer`).
- **Cómo comprobarla**: `cargo test --manifest-path client/src-tauri/Cargo.toml startup` (escribe y borra el valor en un registro falso) y `bun run --cwd client vitest run tests/unit/src/features/settings/StartAtLogin.test.tsx`. Con la app instalada, en la verificación final: activar, `reg query` del valor, desactivar.
- **Pendiente**: el registro real y el arranque del server al iniciar sesión se comprueban en la verificación final (e2e `happy-start-at-login`).

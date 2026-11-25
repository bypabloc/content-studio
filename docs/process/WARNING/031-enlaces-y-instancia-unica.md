# 031: enlaces content-studio:// con deep-link 2.6.3 e instancia única 2.5.5

- **Contexto**: la spec pide `tauri-plugin-deep-link` y `tauri-plugin-single-instance`. `cargo info` da la versión
  3.0.0-alpha.3 (línea de Tauri 3). La línea de Tauri 2 que compila con `tauri =2.12.7` es 2.6.3 y 2.5.5.
- **Elegida**: versiones exactas `=2.6.3` y `=2.5.5` en `client/src-tauri/Cargo.toml`, con la feature `deep-link` de
  single-instance. Dos comandos nuevos: `startup_argv` (el argv con el que arrancó el proceso: un enlace que abre la app
  en frío llega por aquí) y `path_exists` (una ruta de enlace solo rellena si es un archivo que existe).
- **Descartadas**: la línea 3.x alpha (es Tauri 3 y no compila con esta app); escuchar el enlace solo con el plugin de JS
  (no entrega el arranque en frío a una ventana que todavía no se montó); validar la ruta en JS (el client no lee el disco).
- **Cómo revertir**: quitar las dos crates de `Cargo.toml`, el bloque `deep-link` de `tauri.conf.json`, `external.rs` y las
  líneas de `lib.rs` (plugins, `mod external` y los comandos).
- **Cómo comprobarla**: `cargo test --manifest-path client/src-tauri/Cargo.toml external` (3 pruebas) y
  `uv run pytest tests/validators/test_pins.py` (la tabla de `frontend-stack.md` coincide con los manifiestos).
- **Verificado**: tras instalar, `HKCU\Software\Classes\content-studio` existe, y con la app abierta un enlace llega a su ventana (`app-check`, escenario `031-deeplink`).

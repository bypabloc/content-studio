# 025: AC-6 con el instalador real, pendiente de permiso

- **Contexto**: AC-6 pide que la app instalada desde el instalador nuevo, sobre una instalación previa con 3.12, arranque y cargue Narración (03 §2, punto 4). Eso instala y reemplaza la app en la PC del usuario.
- **Elegida**: no se instaló. La prueba de recreación del venv está en `prepare_tests.rs` (`recreates_venv_when_python_changes`) y corre en `cargo test`.
- **Descartadas**: instalar encima de la instalación real del usuario sin su permiso (toca sus datos y su app).
- **Cómo revertir**: no aplica (no hay cambio).
- **Cómo comprobarla**: con permiso del usuario, `python -m devtools bundle`, luego `python -m devtools app-check run --binary=<instalador nuevo> --scenario=installed` sobre una instalación previa, sin tocar `--data=real`.
- **Pendiente**: ver la ficha en `PENDING/` si el usuario decide no instalar antes de `main`.

# 012: los tres `engine.uninstall` que quedaron en Error se conservan como historial

- **Contexto**: en la base real (`var/content-studio.db`) quedaron tres trabajos `engine.uninstall` en Error (IDs 1 a 3) durante las pruebas de desinstalación. Ninguno tocó un motor `external`: la desinstalación externa solo borra el venv conocido (ver `012-desinstalacion-externa.md`).
- **Elegida**: no borrarlos ni reintentarlos. Son historial de trabajos fallidos, no datos del usuario, y borrarlos sin mirar la causa haría perder la evidencia. Quedan como están y se anotan aquí.
- **Descartadas**: borrarlos (oculta el fallo); reintentarlos (la desinstalación sobre motores del equipo podría tocar datos que el usuario usa).
- **Cómo revertir**: no aplica; no se cambió nada.
- **Cómo comprobarla**: `uv run studio jobs list --kind engine` muestra los IDs 1 a 3 en `failed`; `uv run studio engines list` sigue mostrando los motores `external` como `installed`.
- **Pendiente**: el usuario decide si borra esos trabajos en `PENDING/012-instalar-motor-real.md`.
